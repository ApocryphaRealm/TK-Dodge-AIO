#include "ui.h"

#include "InputEvents.h"
#include "Settings.h"

#include "SKSEMenuFramework.h"
#include "utils/Logger.h"
#include "utils/Strings.h"
#include "utils/Toggle.h"

#include <CLIBUtil/hotkeys.hpp>

#include <functional>

namespace Menu
{
	namespace
	{
		using S = Config::Settings;

		std::string g_status;
		std::string g_selectedSlider;

		constexpr const char* kEvents[] = { "TKDodgeBack", "TKDodgeForward", "TKDodgeLeft", "TKDodgeRight" };
		constexpr const char* kEventKeys[] = { "TKD_EventBack", "TKD_EventForward", "TKD_EventLeft", "TKD_EventRight" };
		constexpr const char* kEventNames[] = { "Back", "Forward", "Left", "Right" };

		constexpr const char* kLogKeys[] = { "TKD_LogTrace", "TKD_LogDebug", "TKD_LogInfo", "TKD_LogWarning", "TKD_LogError", "TKD_LogCritical", "TKD_LogOff" };
		constexpr const char* kLogNames[] = { "Trace", "Debug", "Info", "Warning", "Error", "Critical", "Off" };

		void OnMainThread(std::function<void()> a_task)
		{
			if (auto* tasks = SKSE::GetTaskInterface()) {
				tasks->AddTask(std::move(a_task));
			}
		}

		bool HasRequiredExports()
		{
			constexpr const char* required[] = {
				"AddSectionItem", "igTextV", "igTextDisabledV", "igTextWrappedV", "igSetTooltipV", "igSeparatorText",
				"igCombo_Str_arr", "igSliderFloat", "igIsKeyPressed_Bool", "igIsItemClicked", "igIsItemActive",
				"igIsItemHovered", "igButton", "igSameLine", "igSpacing", "igPushItemWidth", "igPopItemWidth",
				"igGetCursorScreenPos", "igGetWindowDrawList", "igGetFrameHeight", "igInvisibleButton", "igPushID_Str",
				"igPopID", "ImDrawList_AddRectFilled", "ImDrawList_AddCircleFilled"
			};
			for (const char* name : required) {
				if (!GetMenuFrameworkFunction<void*>(name)) {
					logger::warn("UI: the menu framework does not export \"{}\"", name);
					return false;
				}
			}
			return true;
		}

		void Help(const char* a_text)
		{
			ImGuiMCP::SameLine();
			ImGuiMCP::TextDisabled("%s", strings::TR("TKD_HelpMark", "(?)"));
			if (ImGuiMCP::IsItemHovered()) {
				ImGuiMCP::SetTooltip("%s", a_text);
			}
		}

		void Switch(const char* a_key, const char* a_label, Config::Value<bool>& a_value, const char* a_helpKey, const char* a_help)
		{
			bool v = a_value.GetValue();
			if (ImGuiMCP::Toggle(strings::TR(a_key, a_label), &v)) {
				a_value.SetValue(v);
				logger::debug("UI: {} -> {}", a_value.key, v);
			}
			Help(strings::TR(a_helpKey, a_help));
		}

		void Slider(const char* a_key, const char* a_label, Config::Value<float>& a_value, float a_min, float a_max,
			const char* a_format, float a_step, const char* a_helpKey, const char* a_help)
		{
			float v = a_value.GetValue();
			const std::string label = strings::TR(a_key, a_label);
			bool changed = ImGuiMCP::SliderFloat(label.c_str(), &v, a_min, a_max, a_format);
			if (ImGuiMCP::IsItemClicked() || ImGuiMCP::IsItemActive()) {
				g_selectedSlider = a_value.key;
			}
			if (g_selectedSlider == a_value.key) {
				float nudge = 0.0F;
				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_LeftArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_DownArrow)) { nudge -= a_step; }
				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_RightArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_UpArrow)) { nudge += a_step; }
				if (nudge != 0.0F) {
					v = std::clamp(v + nudge, a_min, a_max);
					changed = true;
				}
			}
			if (changed) {
				a_value.SetValue(v);
				logger::debug("UI: {} -> {:.2f}", a_value.key, v);
			}
			Help(strings::TR(a_helpKey, a_help));
		}

		// AMF reserved keys (rule 28): whatever the framework reports right now, asked at each capture.
		std::vector<std::int32_t> ReservedKeys()
		{
			using Fn = std::uint32_t (*)(std::int32_t*, std::uint32_t);
			std::vector<std::int32_t> out;
			if (auto fn = GetMenuFrameworkFunction<Fn>("SMF_GetReservedKeyCodes")) {
				std::int32_t buf[32]{};
				const auto n = fn(buf, 32);
				out.assign(buf, buf + std::min<std::uint32_t>(n, 32));
			}
			return out;
		}

		std::string KeyName(std::uint32_t a_key)
		{
			if (a_key <= 1) {
				return strings::TR("TKD_Unbound", "Unbound");
			}
			std::string name(clib_util::hotkeys::details::GetNameByKey(a_key));
			if (name.empty()) {
				name = std::to_string(a_key);
			}
			return name;
		}

		void DrawDodgeKeyRow()
		{
			const auto key = S::dodge_key.GetValue();
			ImGuiMCP::Text("%s: %s", strings::TR("TKD_DodgeKey", "Dodge key"), KeyName(key).c_str());
			ImGuiMCP::SameLine();
			if (!Settings::capture_key_input) {
				if (ImGuiMCP::Button(strings::TR("TKD_Rebind", "Rebind"))) {
					Settings::capture_key_input = true;
					g_status.clear();
					logger::debug("UI: waiting for a key to bind to dodge");
				}
				ImGuiMCP::SameLine();
				if (ImGuiMCP::Button(strings::TR("TKD_Unbind", "Unbind"))) {
					S::dodge_key.SetValue(1);
					logger::debug("UI: dodge key unbound");
				}
			} else {
				ImGuiMCP::Text("%s", strings::TR("TKD_PressKey", "Press a key or controller button..."));
				ImGuiMCP::SameLine();
				if (ImGuiMCP::Button(strings::TR("TKD_Cancel", "Cancel"))) {
					Settings::capture_key_input = false;
				}
			}
			Help(strings::TR("TKD_HelpDodgeKey", "The key or controller button that dodges. Keyboard, mouse and controller buttons all work."));
		}

		void RenderButtons()
		{
			ImGuiMCP::SeparatorText("");
			if (ImGuiMCP::Button(strings::TR("TKD_Save", "Save"))) {
				g_status = strings::TR("TKD_Saving", "Saving...");
				OnMainThread([]() {
					g_status = S::UpdateSettings(true) ? strings::TR("TKD_Saved", "Settings saved.")
					                                   : strings::TR("TKD_SaveFail", "Could not write the INI. See the log for why.");
				});
			}
			Help(strings::TR("TKD_HelpSave", "Writes every setting on this page to the INI so it survives a restart."));
			ImGuiMCP::SameLine();
			if (ImGuiMCP::Button(strings::TR("TKD_Reload", "Reload from INI"))) {
				OnMainThread([]() {
					g_status = S::UpdateSettings(false) ? strings::TR("TKD_Reloaded", "Settings reloaded from the INI.")
					                                    : strings::TR("TKD_ReloadFail", "Could not read the INI. See the log for why.");
					S::ApplyLogLevel();
				});
			}
			Help(strings::TR("TKD_HelpReload", "Throws away unsaved changes and re-reads the INI from disk."));
			ImGuiMCP::SameLine();
			if (ImGuiMCP::Button(strings::TR("TKD_Restore", "Restore defaults"))) {
				OnMainThread([]() { S::RestoreDefaults(); });
				g_status = strings::TR("TKD_Restored", "Defaults restored. Press Save to keep them.");
			}
			Help(strings::TR("TKD_HelpRestore", "Puts every setting back to its fresh-install value. Nothing is written until you press Save."));
			if (!g_status.empty()) {
				ImGuiMCP::TextWrapped("%s", g_status.c_str());
			}
			ImGuiMCP::Spacing();
			ImGuiMCP::Text("%s", S::IniPath().c_str());
		}
	}

	void RegisterDodgeMenu()
	{
		if (!SKSEMenuFramework::IsInstalled()) {
			logger::info("UI: no menu framework installed; settings come from the INI only");
			return;
		}
		if (!HasRequiredExports()) {
			logger::warn("UI: the installed menu framework is too old for this page; update the Apocrypha Menu Framework");
			return;
		}
		SKSEMenuFramework::SetSection("TK Dodge AIO");
		SKSEMenuFramework::AddSectionItem("Settings", Settings::RenderSettings);
		SKSEMenuFramework::AddInputEvent(Settings::OnInput);
		logger::info("UI: settings page registered with the menu framework");
	}

	bool __stdcall Settings::OnInput(RE::InputEvent* a_event)
	{
		if (!capture_key_input) {
			return false;
		}
		for (auto e = a_event; e; e = e->next) {
			const auto button = e->AsButtonEvent();
			if (!button || !button->HasIDCode() || !button->IsDown()) {
				continue;
			}
			const auto key = Events::KeyCodeOf(button);
			if (key == 256) {  // left mouse clicks the page itself; never capture it
				continue;
			}
			const auto reserved = ReservedKeys();
			if (key < 256 && std::find(reserved.begin(), reserved.end(), static_cast<std::int32_t>(key)) != reserved.end()) {
				g_status = std::string(strings::TR("TKD_Reserved", "That key is reserved by the menu framework. Pick another.")) +
				           " (" + KeyName(key) + ")";
				logger::debug("UI: capture refused key {} - reserved by the framework", key);
				return true;
			}
			S::dodge_key.SetValue(key);
			capture_key_input = false;
			g_status = std::string(strings::TR("TKD_Bound", "Dodge bound to")) + " " + KeyName(key) + ". " +
			           strings::TR("TKD_RememberSave", "Press Save to keep it.");
			logger::debug("UI: dodge key captured {}", key);
			return true;
		}
		return false;
	}

	void __stdcall Settings::RenderSettings()
	{
		strings::Tick();

		ImGuiMCP::TextWrapped("%s", strings::TR("TKD_Intro", "Changes apply immediately. Press Save to keep them. After changing the dodge animation patch, run Pandora again."));
		ImGuiMCP::Spacing();
		ImGuiMCP::PushItemWidth(260.0F);

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecDodge", "Dodging"));
		Switch("TKD_StepDodge", "Step dodge instead of roll", S::step_dodge, "TKD_HelpStepDodge", "Short sidesteps instead of rolls.");
		Switch("TKD_InPlace", "Dodge while standing still", S::enable_dodge_in_place, "TKD_HelpInPlace", "Dodging with no direction held uses the default direction below.");
		{
			int current = 0;
			for (int i = 0; i < 4; ++i) {
				if (S::default_dodge_event.GetValue() == kEvents[i]) { current = i; }
			}
			std::vector<std::string> store;
			std::vector<const char*> labels;
			for (int i = 0; i < 4; ++i) { store.emplace_back(strings::TR(kEventKeys[i], kEventNames[i])); }
			for (auto& s : store) { labels.push_back(s.c_str()); }
			if (ImGuiMCP::Combo(strings::TR("TKD_DefaultDir", "Default direction"), &current, labels.data(), 4)) {
				S::default_dodge_event.SetValue(kEvents[current]);
			}
			Help(strings::TR("TKD_HelpDefaultDir", "The direction used when dodging without holding a direction."));
		}
		Switch("TKD_NoForward", "Block forward dodge", S::remove_forward, "TKD_HelpNoForward", "Holding forward does not dodge.");
		Switch("TKD_NoThird", "Only in first person", S::disable_in_third, "TKD_HelpNoThird", "Turns dodging off in third person.");
		Slider("TKD_IFrames", "Invincibility time", S::i_frame_duration, 0.0F, 3.0F, "%.2f s", 0.05F, "TKD_HelpIFrames",
			"How long you cannot be hit after a dodge starts. Needs IFrame Generator RE. Animations with their own i-frame annotations ignore this.");

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecKeys", "Keys"));
		DrawDodgeKeyRow();
		Switch("TKD_DoubleTap", "Double-tap to dodge", S::use_double_tap, "TKD_HelpDoubleTap", "Dodge only when the dodge, sprint or sneak key is pressed twice quickly.");
		Switch("TKD_SprintKey", "Dodge with a tap of Sprint", S::use_sprint_key, "TKD_HelpSprintKey", "A quick tap of the sprint key dodges; holding it sprints.");
		Slider("TKD_SprintTap", "Sprint tap length", S::sprinting_press_duration, 0.05F, 2.0F, "%.2f s", 0.05F, "TKD_HelpSprintTap", "A sprint press shorter than this dodges.");
		Switch("TKD_SneakKey", "Dodge with a tap of Sneak", S::enable_sneak_key_dodge, "TKD_HelpSneakKey", "A quick tap of the sneak key dodges; holding it sneaks.");
		Slider("TKD_SneakTap", "Sneak tap length", S::sneaking_press_duration, 0.05F, 2.0F, "%.2f s", 0.05F, "TKD_HelpSneakTap", "A sneak press shorter than this dodges.");

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecStamina", "Stamina"));
		Slider("TKD_Cost", "Dodge cost", S::dodge_cost, 0.0F, 100.0F, "%.1f", 1.0F, "TKD_HelpCost", "Stamina each dodge uses (or percent of max stamina, below).");
		Switch("TKD_Percent", "Cost is a percentage of max stamina", S::use_percentage_cost, "TKD_HelpPercent", "Treats the dodge cost as a percentage instead of a flat amount.");

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecAttacks", "Attacks and sneaking"));
		Switch("TKD_Cancel", "Dodge cancels attacks", S::enable_dodge_attack_cancel, "TKD_HelpCancel", "A dodge can interrupt your attack.");
		Switch("TKD_LightOnly", "Only cancel light attacks", S::only_cancel_light, "TKD_HelpLightOnly", "Power attacks cannot be cancelled by a dodge.");
		Switch("TKD_MCO", "Only in the MCO recovery window", S::use_mco_recover_window, "TKD_HelpMCO", "With MCO/BFCO, attacks can only be cancelled once their recovery window opens.");
		Switch("TKD_Sneak", "Dodge while sneaking", S::enable_sneak_dodge, "TKD_HelpSneak", "Allows dodging from sneak.");

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecPerks", "Perks and spells"));
		Switch("TKD_PerkLock", "Dodging needs a perk", S::use_perk_lock, "TKD_HelpPerkLock", "Only characters with the dodge perk (set in the INI's [Forms] section) can dodge.");
		ImGuiMCP::TextWrapped("%s %s", strings::TR("TKD_PerkIs", "Dodge perk:"), S::dodge_perk_ID.GetValue().c_str());
		ImGuiMCP::TextWrapped("%s %s", strings::TR("TKD_SpellIs", "On-dodge spell:"), S::on_dodge_spell_ID.GetValue().c_str());
		Help(strings::TR("TKD_HelpForms", "Perk and spell IDs are edited in the INI (Plugin.esp|0x800 or an EditorID), then Reload from INI."));

		ImGuiMCP::SeparatorText(strings::TR("TKD_SecDebug", "Debug"));
		{
			int level = static_cast<int>(std::clamp<std::uint32_t>(S::log_level.GetValue(), 0u, 6u));
			std::vector<std::string> store;
			std::vector<const char*> labels;
			for (int i = 0; i < 7; ++i) { store.emplace_back(strings::TR(kLogKeys[i], kLogNames[i])); }
			for (auto& s : store) { labels.push_back(s.c_str()); }
			if (ImGuiMCP::Combo(strings::TR("TKD_LogLevel", "Log level"), &level, labels.data(), 7)) {
				S::log_level.SetValue(static_cast<std::uint32_t>(level));
				S::ApplyLogLevel();
			}
			Help(strings::TR("TKD_HelpLog", "Applies immediately. The log is Documents\\My Games\\Skyrim Special Edition\\SKSE\\TK Dodge AIO.log."));
		}

		ImGuiMCP::PopItemWidth();
		RenderButtons();
	}
}
