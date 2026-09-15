#include "InputEvents.h"

#include "Settings.h"
#include "Utility.h"
#include "dodging.h"
#include "ui.h"
#include "utils/Logger.h"

namespace Events
{
	std::uint32_t KeyCodeOf(const RE::ButtonEvent* a_button)
	{
		std::uint32_t id = a_button->GetIDCode();
		switch (a_button->GetDevice()) {
		case RE::INPUT_DEVICE::kMouse:
			id += SKSE::InputMap::kMacro_MouseButtonOffset;
			break;
		case RE::INPUT_DEVICE::kGamepad:
			id = SKSE::InputMap::GamepadMaskToKeycode(id);
			break;
		default:
			break;
		}
		return id;
	}

	void InputEvent::RegisterInput()
	{
		if (const auto manager = RE::BSInputDeviceManager::GetSingleton()) {
			manager->AddEventSink(this);
			logger::info("Input: listening for the dodge key (key code {})", Config::Settings::dodge_key.GetValue());
		} else {
			logger::error("Input: BSInputDeviceManager is null; the dodge key cannot be read (sprint/sneak-key dodge still can)");
		}
	}

	EventResult InputEvent::ProcessEvent(RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>*)
	{
		if (!a_event) {
			return EventResult::kContinue;
		}
		// While the settings page is capturing a new key, the press belongs to the page, not to a dodge.
		if (Menu::Settings::capture_key_input) {
			return EventResult::kContinue;
		}

		const auto bound = Config::Settings::dodge_key.GetValue();
		for (auto e = *a_event; e; e = e->next) {
			const auto button = e->AsButtonEvent();
			if (!button || !button->IsDown() || !button->HasIDCode()) {
				continue;
			}
			const auto id = KeyCodeOf(button);
			if (bound <= 1 || id != bound) {
				continue;
			}
			if (Utility::IsInMenu()) {
				logger::trace("Dodge key {} pressed in a menu - ignored", id);
				continue;
			}
			logger::debug("Dodge key {} pressed", id);
			Dodge::OnInput();
		}
		return EventResult::kContinue;
	}
}
