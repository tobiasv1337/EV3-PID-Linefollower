from ev3dev2.display import Display
import time

display = Display()

screen_width = 178
screen_height = 128

def draw_quarters():
    quarters = [
        ((0, 0, screen_width // 2 - 1, screen_height // 2 - 1), (5, 5)),  # Top-left
        ((screen_width // 2, 0, screen_width - 1, screen_height // 2 - 1), (screen_width // 2 + 5, 5)),  # Top-right
        ((0, screen_height // 2, screen_width // 2 - 1, screen_height - 1), (5, screen_height // 2 + 5)),  # Bottom-left
        ((screen_width // 2, screen_height // 2, screen_width - 1, screen_height - 1), (screen_width // 2 + 5, screen_height // 2 + 5))  # Bottom-right
    ]

    for i, (rect, text_pos) in enumerate(quarters):
        display.clear()

        display.draw.rectangle(rect, fill='black')

        display.draw.text(text_pos, "Quarter %d" % (i + 1), fill='white')

        display.update()
        time.sleep(1.5)

draw_quarters()