#pragma once

#include <string_view>

struct MOD
{
	inline static constexpr std::string_view INI_FILE = "TK Dodge AIO.ini";
	inline static constexpr std::string_view LOG_NAME = "TK Dodge AIO";

	// The Addon's plugin, shipped unchanged so perk mods built against it keep working.
	inline static constexpr std::string_view MOD_NAME = "TKDodgeAddon.esp";

	inline static constexpr RE::FormID DUMMY_SPELL_LOCK_PERK_FORMID = 0x80F;
	inline static constexpr RE::FormID DUMMY_DODGE_SPELL_FORMID = 0x811;
	inline static constexpr RE::FormID DODGE_PERK_DUMMY_FORMID = 0x809;

	inline static constexpr std::string_view USED_AV = "DodgeCostModifier";
	inline static constexpr std::string_view EXTRA_DODGE_AV = "ExtraDodgeCostModifier";

	inline static constexpr std::string_view DODGE_COST_PERK = "ModDodgeCost";
	inline static constexpr std::string_view IFRAME_DURATION_PERK = "ModiFrameDuration";
};
