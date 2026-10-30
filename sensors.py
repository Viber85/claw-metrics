"""Read-only battery discharge power. Invoked by MangoHud's exec element."""
from pathlib import Path


def draw(root=Path('/sys/class/power_supply')):
    try:
        for battery in sorted(root.glob('*')):
            if (battery / 'type').read_text().strip() != 'Battery':
                continue
            # Charging power is not total device consumption.
            if (battery / 'status').read_text().strip() != 'Discharging':
                return 'DRAW --'
            power = battery / 'power_now'
            watts = (abs(int(power.read_text())) / 1_000_000 if power.is_file()
                     else abs(int((battery / 'current_now').read_text()) *
                              int((battery / 'voltage_now').read_text())) / 1_000_000_000_000)
            return f'DRAW {watts:.1f}W'
    except (OSError, ValueError):
        pass
    return 'DRAW --'


if __name__ == '__main__':
    print(draw())
