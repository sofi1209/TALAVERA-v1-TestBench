"""Umbilical (cable B) pin map - the single source of truth.

Imported by gen_bench.py, gen_station.py and trace_fire_loop.py, so the two
boards cannot drift apart and the short-matrix check judges adjacency against
the same map that was drawn.

Batch 2, 10 November 2026 - PROVISIONAL, not approved. Chosen from a computed
single-short matrix over every conductor pair (trace_fire_loop.py): no two
ADJACENT pins can fire the bench, arm it, or defeat both E-STOP channels.

ASSUMPTION, unverified: adjacency is linear with pin 12 wrapping to pin 1 (a
circular connector). The real connector part and the cable lay-up are not
chosen. A two-row connector or a different conductor order in the cable makes
other pairs adjacent - re-run the matrix against the real geometry.
"""

# (pin, net). Pin 12 is the shield: bench ground at the bench end only, floating
# at the station end, so it is not listed here - each generator draws it.
PINS = [
    ('1', "FIRE_P"),           # floating FIRE loop, + side   (twisted pair with 2)
    ('2', "FIRE_N"),           # floating FIRE loop, - side
    ('3', "ARM_LINE"),
    ('4', "GND"),
    ('5', "RS485_A"),
    ('6', "RS485_B"),
    ('7', "GND"),
    ('8', "PYRO_CONT_SENSE"),  # active-high continuity sense
    ('9', "VBAT_SENSE"),
    ('10', "ESTOP_LOOP"),      # E-STOP channel 1 (K4 coil low side)
    ('11', "TEST_LINE"),       # continuity TEST command (K3 only)
]
SHIELD_PIN = '12'
N_PINS = 12


def adjacent_pairs():
    """Pin-number pairs treated as physically adjacent (ASSUMED linear + wrap)."""
    return [(str(i), str(i % N_PINS + 1)) for i in range(1, N_PINS + 1)]
