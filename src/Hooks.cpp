#include "Hooks.h"

#include "Settings.h"
#include "Utility.h"
#include "dodging.h"
#include "utils/Logger.h"

namespace Hooks
{
	static bool bStoppingSprint = false;
	static bool bStopSneak = false;

	void SprintHandlerHook::ProcessButton(RE::SprintHandler* a_this, RE::ButtonEvent* a_event, RE::PlayerControlsData* a_data)
	{
		if (a_event && Config::Settings::use_sprint_key.GetValue()) {
			const auto player = RE::PlayerCharacter::GetSingleton();
			const auto userEvents = RE::UserEvents::GetSingleton();
			if (player && userEvents && a_event->QUserEvent() == userEvents->sprint) {
				const bool sprinting = player->GetPlayerRuntimeData().playerFlags.isSprinting;
				if (a_event->IsDown() && sprinting) {
					bStoppingSprint = true;  // this press ends a sprint rather than starting a dodge
				} else if (a_event->HeldDuration() < Config::Settings::sprinting_press_duration.GetValue()) {
					if (a_event->IsUp()) {
						if (!Utility::IsInMenu()) {
							logger::debug("Sprint key tapped ({:.2f}s) - dodge input", a_event->HeldDuration());
							Dodge::OnInput();
						}
						bStoppingSprint = false;
					}
					return;  // a short tap is the dodge, not a sprint
				} else if (!sprinting && !bStoppingSprint) {
					a_event->heldDownSecs = 0.0F;
				} else if (a_event->IsUp()) {
					bStoppingSprint = false;
				}
			}
		}
		_original(a_this, a_event, a_data);
	}

	void SneakHandlerHook::ProcessButton(RE::SneakHandler* a_this, RE::ButtonEvent* a_event, RE::PlayerControlsData* a_data)
	{
		if (a_event && Config::Settings::enable_sneak_key_dodge.GetValue()) {
			const auto player = RE::PlayerCharacter::GetSingleton();
			const auto userEvents = RE::UserEvents::GetSingleton();
			if (player && userEvents && a_event->QUserEvent() == userEvents->sneak) {
				if (a_event->IsDown() && player->IsSneaking()) {
					bStopSneak = true;
				} else if (a_event->HeldDuration() < Config::Settings::sneaking_press_duration.GetValue()) {
					if (a_event->IsUp()) {
						if (!Utility::IsInMenu()) {
							logger::debug("Sneak key tapped ({:.2f}s) - dodge input", a_event->HeldDuration());
							Dodge::OnInput();
						}
						bStopSneak = false;
					}
					return;
				} else if (!player->IsSneaking() && !bStopSneak) {
					a_event->heldDownSecs = 0.0F;
				} else if (a_event->IsUp()) {
					bStopSneak = false;
				}
			}
		}
		_original(a_this, a_event, a_data);
	}

	void PlayerUpdateLoop::PlayerUpdate(RE::PlayerCharacter* a_this, float a_delta)
	{
		if (a_this && !a_this->IsAttacking()) {
			a_this->SetGraphVariableBool("DodgeCancelEnabled", true);
		}
		_original(a_this, a_delta);
	}

	static bool wasInMenu = false;

	std::uintptr_t MainUpdateLoop::Thunk(std::uintptr_t a_rcx, std::uintptr_t a_rdx, std::uintptr_t a_r8, std::uintptr_t a_r9)
	{
		const bool inMenu = Utility::IsInMenu();
		if (wasInMenu != inMenu) {
			logger::debug("Menu state changed: {}", inMenu ? "a blocking menu opened" : "back to gameplay");
		}
		if (wasInMenu && !inMenu) {
			Dodge::g_menuBlocker.block();
			Dodge::ClearBuffer();
		}
		if (Dodge::g_menuBlocker.active()) {
			Dodge::ClearBuffer();
		} else if (auto* player = RE::PlayerCharacter::GetSingleton()) {
			Dodge::Update(player);
		}
		wasInMenu = inMenu;

		return _original(a_rcx, a_rdx, a_r8, a_r9);
	}

	void Install()
	{
		REL::Relocation<std::uintptr_t> sprintVtbl{ RE::VTABLE_SprintHandler[0] };
		SprintHandlerHook::_original = sprintVtbl.write_vfunc(0x4, SprintHandlerHook::ProcessButton);
		logger::info("Hook: SprintHandler::ProcessButton (vtable {:X} slot 0x4)", sprintVtbl.address());

		REL::Relocation<std::uintptr_t> sneakVtbl{ RE::VTABLE_SneakHandler[0] };
		SneakHandlerHook::_original = sneakVtbl.write_vfunc(0x4, SneakHandlerHook::ProcessButton);
		logger::info("Hook: SneakHandler::ProcessButton (vtable {:X} slot 0x4)", sneakVtbl.address());

		REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerCharacter[0] };
		PlayerUpdateLoop::_original = playerVtbl.write_vfunc(0xAD, PlayerUpdateLoop::PlayerUpdate);
		logger::info("Hook: PlayerCharacter::Update (vtable {:X} slot 0xAD)", playerVtbl.address());

		REL::Relocation<std::uintptr_t> mainLoop{ RELOCATION_ID(35565, 36564), REL::Relocate(0x731, 0xC26) };
		const auto site = mainLoop.address();
		if (*reinterpret_cast<std::uint8_t*>(site) != 0xE8) {
			logger::critical("Hook: the main-loop call site {:X} is not a call (byte {:02X}) - another plugin patched it or this "
							 "game build differs. Dodging will not fire; nothing was written there.",
				site, *reinterpret_cast<std::uint8_t*>(site));
			return;
		}
		auto& trampoline = SKSE::GetTrampoline();
		MainUpdateLoop::_original = trampoline.write_call<5>(site, MainUpdateLoop::Thunk);
		logger::info("Hook: main loop update call at {:X} (original target {:X})", site, MainUpdateLoop::_original.address());
	}
}
