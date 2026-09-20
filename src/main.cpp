// TK Dodge AIO - TK Dodge RE (Maxsu et al., MIT) + TK Dodge RE Addon (Styyx, GPL-3.0), ported to Skyrim SE
// 1.5.97 on CommonLibSSE-NG with its settings page on the Apocrypha Menu Framework. GPL-3.0-or-later.
#include "AnimationEvents.h"
#include "Hooks.h"
#include "InputEvents.h"
#include "Settings.h"
#include "ui.h"

#include "utils/AddressLibraryGuard.h"
#include "utils/Logger.h"
#include "utils/Strings.h"

namespace
{
	void Listener(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kInputLoaded:
			logger::debug("kInputLoaded: registering the dodge key listener");
			Events::InputEvent::GetSingleton()->RegisterInput();
			Events::MenuEvent::GetSingleton()->RegisterMenus();
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			logger::debug("kDataLoaded: animation-event sink, forms, strings, settings page");
			animEventHandler::RegisterForPlayer();
			Config::Forms::LoadForms();
			strings::Configure("TK Dodge AIO");
			Menu::RegisterDodgeMenu();
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	// The log first, then the Address Library guard, then SKSE::Init - in that order. CommonLibSSE-NG's
	// Init opens the Address Library itself, so a guard placed after it never ran when the file was
	// missing (oproso's wheeler.log, 2026-09-18); and the guard's own line has to land in a log that exists.
	// When the file for this game is missing the plugin loads inert with a message that names it.
	SKSE::log::init(std::string(MOD::LOG_NAME));
	if (!AddressLibraryGuard::Guard("TK Dodge AIO")) {
		return true;
	}
	SKSE::Init(a_skse);

	Config::Settings::UpdateSettings(false);
	Config::Settings::ApplyLogLevel();
	SKSE::log::describe_level(std::string(MOD::INI_FILE));

	logger::info("TK Dodge AIO {} loading on Skyrim {}", SKSE::PluginDeclaration::GetSingleton()->GetVersion().string("."),
		REL::Module::get().version().string("."));

	SKSE::AllocTrampoline(64);
	Hooks::Install();

	const auto messaging = SKSE::GetMessagingInterface();
	if (!messaging || !messaging->RegisterListener(Listener)) {
		logger::critical("Could not register for SKSE messages; TK Dodge AIO cannot start");
		return false;
	}
	return true;
}
