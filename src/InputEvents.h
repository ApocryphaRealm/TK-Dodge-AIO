#pragma once

namespace Events
{
	using EventResult = RE::BSEventNotifyControl;

	struct InputEvent : RE::BSTEventSink<RE::InputEvent*>
	{
		static InputEvent* GetSingleton()
		{
			static InputEvent singleton;
			return std::addressof(singleton);
		}

		void        RegisterInput();
		EventResult ProcessEvent(RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>*) override;

	private:
		InputEvent() = default;
	};

	// SKSE key code for a button event: 0-255 keyboard, 256+ mouse, 266+ gamepad (SKSE InputMap layout).
	std::uint32_t KeyCodeOf(const RE::ButtonEvent* a_button);
}
