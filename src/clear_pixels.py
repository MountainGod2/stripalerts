import board
import neopixel

pixel_pin = board.D18

num_pixels = 100


pixels = neopixel.NeoPixel(
    pixel_pin, # type: ignore
    num_pixels,
    brightness=0.2,
    auto_write=False,  # type: ignore
)

pixels.fill((0, 0, 0))
pixels.show()
pixels.deinit()
