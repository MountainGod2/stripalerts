"""LEDController class."""

import asyncio
import logging
import time

from adafruit_led_animation.animation import (pulse, rainbow, rainbowsparkle,
                                              solid)
from adafruit_led_animation.sequence import AnimationSequence

from alert_colors_enum import AlertColor
from constants import (ALERT_DURATION, ANIMATION_SPEED, COLOR_DURATION,
                       PULSE_PERIOD, PULSE_SPEED, RAINBOW_PERIOD,
                       RAINBOW_SPEED, SECONDS_PER_MIN, SPARKLE_BASE_BRIGHTNESS,
                       SPARKLE_NUM_SPARKLES, SPARKLE_PERIOD, SPARKLE_SPEED)


class LEDController:
    """
    Class to control the LED animations.

    Attributes:
        pixels (neopixel.NeoPixel): NeoPixel LED strip.
        animations (AnimationSequence): Animation sequence.
        current_color (AlertColor): Current color alert.
        color_set_time (float): Time when the current color alert was set.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self, pixels):
        self.pixels = pixels
        self.animations = self.create_animations()
        self.current_color = None
        self.color_set_time = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_animations(self):
        """
        Create the animation sequence.

        Returns:
            AnimationSequence: Animation sequence.
        """
        rainbow_animation = rainbow.Rainbow(
            self.pixels, speed=RAINBOW_SPEED, period=RAINBOW_PERIOD, name="rainbow"
        )
        sparkle_animation = rainbowsparkle.RainbowSparkle(
            self.pixels,
            speed=SPARKLE_SPEED,
            period=SPARKLE_PERIOD,
            num_sparkles=SPARKLE_NUM_SPARKLES,
            background_brightness=SPARKLE_BASE_BRIGHTNESS,
            name="sparkle",
        )
        pulse_animations = [
            pulse.Pulse(
                self.pixels,
                speed=PULSE_SPEED,
                color=color.value,
                period=PULSE_PERIOD,
                name=f"{color.name}_pulse",
            )
            for color in AlertColor
        ]
        solid_animations = [
            solid.Solid(self.pixels, color=color.value, name=f"{color.name}")
            for color in AlertColor
        ]

        return AnimationSequence(
            rainbow_animation,
            sparkle_animation,
            *pulse_animations,
            *solid_animations,
            advance_interval=None,
            auto_clear=True,
        )

    async def run_animation_loop(self):
        """Run the animation loop."""
        while True:
            if (
                self.current_color
                and self.color_set_time
                and (time.time() - self.color_set_time > COLOR_DURATION)
            ):
                self.current_color = None
                self.logger.info("Color alert duration expired. Resetting to rainbow.")
                self.animations.activate("rainbow")
            self.animations.animate()
            await asyncio.sleep(ANIMATION_SPEED)

    async def trigger_normal_alert(self):
        """Trigger the normal alert."""
        previous_state = self.animations.current_animation.name
        self.logger.debug("Activating normal alert.")
        self.animations.activate("sparkle")
        await asyncio.sleep(ALERT_DURATION)
        self.animations.activate(previous_state)

    async def trigger_color_alert(self, color):
        """
        Trigger the color alert.

        Args:
            color (AlertColor): Color alert to activate.
        """
        self.current_color = color
        self.color_set_time = time.time()
        self.logger.debug(f"Activating color alert: {color.name.lower()}.")
        self.animations.activate(f"{color.name}_pulse")
        await asyncio.sleep(ALERT_DURATION)
        color_time = (
            f"{COLOR_DURATION} seconds"
            if COLOR_DURATION < SECONDS_PER_MIN
            else f"{COLOR_DURATION // SECONDS_PER_MIN} minutes"
        )
        self.logger.info(f"Setting lights to {color.name.lower()} for {color_time}.")
        self.animations.activate(color.name)

    async def stop_animation(self):
        """Stop the animation loop."""
        self.animations.freeze()
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        self.pixels.deinit()
        await asyncio.sleep(0)
