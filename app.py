import pygame
import random
import math
import sys
import os
import json
import urllib.request
import hashlib
import time

try:
    import pyperclip
    HAS_CLIPBOARD = True
except:
    HAS_CLIPBOARD = False

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
MAX_ENEMIES = 10
PI_2 = math.pi * 2

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
RED = (220, 50, 50)
GOLD = (255, 215, 0)
HUMAN_COLOR = (50, 100, 200)
BG_COLOR = (30, 30, 35)

# Rarity colors
RARITY_COLORS = {
    'common':    (200, 200, 200),
    'rare':      (80, 150, 255),
    'epic':      (200, 80, 255),
    'legendary': (255, 180, 50),
}
RARITY_WEIGHTS = {'common': 60, 'rare': 25, 'epic': 12, 'legendary': 3}

# --- Game States ---
STATE_MENU = 0
STATE_DIFFICULTY = 1
STATE_PLAYING = 2
STATE_PAUSED = 3
STATE_WIN = 4
STATE_LOSE = 5
STATE_ACHIEVEMENTS = 6
STATE_TUTORIAL = 7
STATE_WAVE_TRANSITION = 8
STATE_UPGRADE = 9  # NEW: Choose upgrade

# =====================================================================
# UPGRADE SYSTEM
# =====================================================================
UPGRADES = [
    # ============ UNIVERSAL - COMMON ============
    {'id': 'hp_up',        'name': 'Vitality',         'icon': '❤️', 'rarity': 'common',    'classes': None, 'max_stacks': 3,
     'desc': '+1 Max HP', 'effect': lambda p: setattr(p, 'max_hp', p.max_hp + 1) or setattr(p, 'hp', p.hp + 1)},
    {'id': 'speed_up',     'name': 'Swift Feet',       'icon': '👟', 'rarity': 'common',    'classes': None, 'max_stacks': 3,
     'desc': '+10% Move Speed', 'effect': lambda p: setattr(p, 'base_speed', p.base_speed * 1.1)},
    {'id': 'damage_up',    'name': 'Sharp Claws',      'icon': '🗡️', 'rarity': 'common',    'classes': None, 'max_stacks': 5,
     'desc': '+1 Bump Damage', 'effect': lambda p: setattr(p, 'bump_damage', getattr(p, 'bump_damage', 1) + 1)},
    {'id': 'aura_up',      'name': 'Expanded Reach',   'icon': '🔮', 'rarity': 'common',    'classes': None, 'max_stacks': 3,
     'desc': '+15% Aura/Radius', 'effect': lambda p: setattr(p, 'radius', int(p.radius * 1.15))},
    {'id': 'lucky',        'name': 'Lucky Charm',      'icon': '🍀', 'rarity': 'common',    'classes': None, 'max_stacks': 3,
     'desc': '+5% Critical Chance', 'effect': lambda p: setattr(p, 'crit_bonus', getattr(p, 'crit_bonus', 0) + 0.05)},
    {'id': 'thick_skin',   'name': 'Thick Skin',       'icon': '🛡️', 'rarity': 'common',    'classes': None, 'max_stacks': 2,
     'desc': '+15s longer i-frames', 'effect': lambda p: setattr(p, 'iframe_bonus', getattr(p, 'iframe_bonus', 0) + 15)},

    # ============ UNIVERSAL - RARE ============
    {'id': 'vampiric',     'name': 'Vampiric Touch',   'icon': '🩸', 'rarity': 'rare',      'classes': None, 'max_stacks': 1,
     'desc': 'Heal 1 HP every 5 conversions', 'effect': lambda p: setattr(p, 'vampiric', True)},
    {'id': 'golden_touch', 'name': 'Golden Touch',     'icon': '✨', 'rarity': 'rare',      'classes': None, 'max_stacks': 2,
     'desc': '+20% Golden Human chance', 'effect': lambda p: setattr(p, 'golden_bonus', getattr(p, 'golden_bonus', 0) + 0.2)},
    {'id': 'power_duration','name': 'Extended Power',  'icon': '⏳', 'rarity': 'rare',      'classes': None, 'max_stacks': 2,
     'desc': '+30% Power-up duration', 'effect': lambda p: setattr(p, 'power_duration_mult', getattr(p, 'power_duration_mult', 1.0) * 1.3)},
    {'id': 'combo_master', 'name': 'Combo Master',     'icon': '🔥', 'rarity': 'rare',      'classes': None, 'max_stacks': 2,
     'desc': 'Combo timer lasts 50% longer', 'effect': lambda p: setattr(p, 'combo_timer_mult', getattr(p, 'combo_timer_mult', 1.0) * 1.5)},
    {'id': 'score_boost',  'name': 'Score Boost',      'icon': '💰', 'rarity': 'rare',      'classes': None, 'max_stacks': 3,
     'desc': '+15% Score multiplier', 'effect': lambda p: setattr(p, 'score_mult', getattr(p, 'score_mult', 1.0) * 1.15)},

    # ============ UNIVERSAL - EPIC ============
    {'id': 'berserker',    'name': 'Berserker',        'icon': '💢', 'rarity': 'epic',      'classes': None, 'max_stacks': 1,
     'desc': '+30% speed when below 50% HP', 'effect': lambda p: setattr(p, 'berserker', True)},
    {'id': 'second_wind',  'name': 'Second Wind',      'icon': '🌬️', 'rarity': 'epic',      'classes': None, 'max_stacks': 1,
     'desc': 'Revive once per run with 1 HP', 'effect': lambda p: setattr(p, 'second_wind', True)},
    {'id': 'magnet',       'name': 'Power Magnet',     'icon': '🧲', 'rarity': 'epic',      'classes': None, 'max_stacks': 1,
     'desc': 'Power-ups attract to you', 'effect': lambda p: setattr(p, 'magnet', True)},

    # ============ UNIVERSAL - LEGENDARY ============
    {'id': 'godhood',      'name': 'Ascension',        'icon': '👑', 'rarity': 'legendary', 'classes': None, 'max_stacks': 1,
     'desc': '+2 Max HP, +20% speed, +1 damage', 'effect': lambda p: (setattr(p, 'max_hp', p.max_hp + 2), setattr(p, 'hp', p.hp + 2), setattr(p, 'base_speed', p.base_speed * 1.2), setattr(p, 'bump_damage', getattr(p, 'bump_damage', 1) + 1))},
    {'id': 'time_stop',    'name': 'Chrono Shift',     'icon': '⏰', 'rarity': 'legendary', 'classes': None, 'max_stacks': 1,
     'desc': 'On wave start: 3s slow-mo', 'effect': lambda p: setattr(p, 'chrono_start', True)},

    # ============ VAMPIRE ============
    {'id': 'vamp_crimson', 'name': 'Crimson Aura',     'icon': '🔴', 'rarity': 'rare',      'classes': ['vampire'], 'max_stacks': 2,
     'desc': '+25% Conversion Aura', 'effect': lambda p: setattr(p, 'aura', int(p.aura * 1.25) if p.aura > 0 else 20)},
    {'id': 'vamp_night',   'name': 'Night Stalker',    'icon': '🌙', 'rarity': 'epic',      'classes': ['vampire'], 'max_stacks': 1,
     'desc': 'I-frames last 50% longer', 'effect': lambda p: setattr(p, 'iframe_mult', getattr(p, 'iframe_mult', 1.0) * 1.5)},
    {'id': 'vamp_blood',   'name': 'Blood Frenzy',     'icon': '🩸', 'rarity': 'legendary', 'classes': ['vampire'], 'max_stacks': 1,
     'desc': 'Each conversion heals 1 HP (max)', 'effect': lambda p: setattr(p, 'blood_frenzy', True)},

    # ============ ZOMBIE ============
    {'id': 'zomb_mass',    'name': 'Undead Mass',      'icon': '💪', 'rarity': 'rare',      'classes': ['zombie'], 'max_stacks': 2,
     'desc': '+25% Size (more bump area)', 'effect': lambda p: setattr(p, 'radius', int(p.radius * 1.25))},
    {'id': 'zomb_rot',     'name': 'Rotting Touch',    'icon': '☠️', 'rarity': 'epic',      'classes': ['zombie'], 'max_stacks': 1,
     'desc': 'Minions move 30% faster', 'effect': lambda p: setattr(p, 'minion_speed_mult', getattr(p, 'minion_speed_mult', 1.0) * 1.3)},
    {'id': 'zomb_regen',   'name': 'Regeneration',     'icon': '💚', 'rarity': 'legendary', 'classes': ['zombie'], 'max_stacks': 1,
     'desc': 'Heal 1 HP every 15 seconds', 'effect': lambda p: setattr(p, 'regen', True)},

    # ============ WITCH ============
    {'id': 'witch_arcane', 'name': 'Arcane Mastery',   'icon': '🔮', 'rarity': 'rare',      'classes': ['witch'], 'max_stacks': 3,
     'desc': '+30% Aura radius', 'effect': lambda p: setattr(p, 'aura', int(p.aura * 1.3))},
    {'id': 'witch_echo',   'name': 'Spell Echo',       'icon': '💫', 'rarity': 'epic',      'classes': ['witch'], 'max_stacks': 1,
     'desc': 'Aura pulses every 2s (converts nearby)', 'effect': lambda p: setattr(p, 'spell_echo', True)},
    {'id': 'witch_coven',  'name': 'Coven Power',      'icon': '🧙', 'rarity': 'legendary', 'classes': ['witch'], 'max_stacks': 1,
     'desc': 'Minions have small conversion aura', 'effect': lambda p: setattr(p, 'minion_aura', 30)},

    # ============ WEREWOLF ============
    {'id': 'wolf_frenzy',  'name': 'Frenzy',           'icon': '🌪️', 'rarity': 'rare',      'classes': ['werewolf'], 'max_stacks': 2,
     'desc': '+50% speed gain per kill', 'effect': lambda p: setattr(p, 'frenzy_mult', getattr(p, 'frenzy_mult', 1.0) * 1.5)},
    {'id': 'wolf_howl',    'name': 'Moon Howl',        'icon': '🌕', 'rarity': 'epic',      'classes': ['werewolf'], 'max_stacks': 1,
     'desc': 'SPACE: Dash forward (10s CD)', 'effect': lambda p: setattr(p, 'howl_dash', True)},
    {'id': 'wolf_pack',    'name': 'Pack Leader',      'icon': '🐺', 'rarity': 'legendary', 'classes': ['werewolf'], 'max_stacks': 1,
     'desc': 'Minions gain +30% speed', 'effect': lambda p: setattr(p, 'minion_speed_mult', getattr(p, 'minion_speed_mult', 1.0) * 1.3)},

    # ============ GHOST ============
    {'id': 'ghost_trail',  'name': 'Ethereal Trail',   'icon': '💨', 'rarity': 'rare',      'classes': ['ghost'], 'max_stacks': 3,
     'desc': 'Trail lasts 50% longer', 'effect': lambda p: setattr(p, 'trail_life_mult', getattr(p, 'trail_life_mult', 1.0) * 1.5)},
    {'id': 'ghost_polter', 'name': 'Poltergeist',      'icon': '👻', 'rarity': 'epic',      'classes': ['ghost'], 'max_stacks': 1,
     'desc': 'Trail damages enemies on contact', 'effect': lambda p: setattr(p, 'trail_damage', 1)},
    {'id': 'ghost_haunt',  'name': 'Haunting Presence','icon': '🕯️', 'rarity': 'legendary', 'classes': ['ghost'], 'max_stacks': 1,
     'desc': 'Trail is 2x wider', 'effect': lambda p: setattr(p, 'trail_width_mult', getattr(p, 'trail_width_mult', 1.0) * 2.0)},

    # ============ ALIEN ============
    {'id': 'alien_plasma', 'name': 'Plasma Cannon',    'icon': '🔫', 'rarity': 'rare',      'classes': ['alien'], 'max_stacks': 3,
     'desc': '-20% Beam cooldown', 'effect': lambda p: setattr(p, 'beam_cd_mult', getattr(p, 'beam_cd_mult', 1.0) * 0.8)},
    {'id': 'alien_abduct', 'name': 'Abduction Beam',   'icon': '🛸', 'rarity': 'epic',      'classes': ['alien'], 'max_stacks': 1,
     'desc': 'Beam converts in small area', 'effect': lambda p: setattr(p, 'beam_aoe', 30)},
    {'id': 'alien_mother', 'name': 'Mothership Strike','icon': '🚀', 'rarity': 'legendary', 'classes': ['alien'], 'max_stacks': 1,
     'desc': 'SPACE (when beam ready): Orbital strike AOE', 'effect': lambda p: setattr(p, 'orbital_strike', True)},

    # ============ SHADOW ============
    {'id': 'shadow_blink', 'name': 'Blink Mastery',    'icon': '💨', 'rarity': 'rare',      'classes': ['shadow'], 'max_stacks': 3,
     'desc': '-25% Dash cooldown', 'effect': lambda p: setattr(p, 'dash_cd_mult', getattr(p, 'dash_cd_mult', 1.0) * 0.75)},
    {'id': 'shadow_clone', 'name': 'Shadow Clone',     'icon': '🥷', 'rarity': 'epic',      'classes': ['shadow'], 'max_stacks': 1,
     'desc': 'Dash leaves decoy that converts', 'effect': lambda p: setattr(p, 'shadow_clone', True)},
    {'id': 'shadow_void',  'name': 'Void Step',        'icon': '🌑', 'rarity': 'legendary', 'classes': ['shadow'], 'max_stacks': 1,
     'desc': 'Dash goes 2x further', 'effect': lambda p: setattr(p, 'dash_distance', getattr(p, 'dash_distance', 120) * 2)},

    # ============ NECROMANCER ============
    {'id': 'necro_grave',  'name': 'Grave Robber',     'icon': '⚰️', 'rarity': 'rare',      'classes': ['necromancer'], 'max_stacks': 2,
     'desc': '+1 Max grave', 'effect': lambda p: setattr(p, 'max_graves', getattr(p, 'max_graves', 3) + 1)},
    {'id': 'necro_harvest','name': 'Soul Harvest',     'icon': '💀', 'rarity': 'epic',      'classes': ['necromancer'], 'max_stacks': 1,
     'desc': 'Graves convert 2x faster (bigger range)', 'effect': lambda p: setattr(p, 'grave_range', getattr(p, 'grave_range', 36) + 15)},
    {'id': 'necro_phyl',   'name': 'Phylactery',       'icon': '💎', 'rarity': 'legendary', 'classes': ['necromancer'], 'max_stacks': 1,
     'desc': 'Revive once per wave at full HP', 'effect': lambda p: setattr(p, 'phylactery', True)},

    # ============ SLIME ============
    {'id': 'slime_ooze',   'name': 'Ooze Master',      'icon': '💧', 'rarity': 'rare',      'classes': ['slime'], 'max_stacks': 3,
     'desc': 'Puddles 20% bigger', 'effect': lambda p: setattr(p, 'puddle_size_mult', getattr(p, 'puddle_size_mult', 1.0) * 1.2)},
    {'id': 'slime_toxic',  'name': 'Toxic Slime',      'icon': '☣️', 'rarity': 'epic',      'classes': ['slime'], 'max_stacks': 1,
     'desc': 'Puddles damage enemies', 'effect': lambda p: setattr(p, 'puddle_damage', 1)},
    {'id': 'slime_split',  'name': 'Split Form',       'icon': '🟢', 'rarity': 'legendary', 'classes': ['slime'], 'max_stacks': 1,
     'desc': 'On hit: Leave giant puddle', 'effect': lambda p: setattr(p, 'split_on_hit', True)},

    # ============ SIREN ============
    {'id': 'siren_voice',  'name': 'Enchanting Voice', 'icon': '🎵', 'rarity': 'rare',      'classes': ['siren'], 'max_stacks': 3,
     'desc': '+30% Charm duration', 'effect': lambda p: setattr(p, 'charm_duration_mult', getattr(p, 'charm_duration_mult', 1.0) * 1.3)},
    {'id': 'siren_call',   'name': "Siren's Call",     'icon': '🎶', 'rarity': 'epic',      'classes': ['siren'], 'max_stacks': 1,
     'desc': 'Charmed enemies take damage over time', 'effect': lambda p: setattr(p, 'charm_damage', True)},
    {'id': 'siren_hypno',  'name': 'Hypnotic Song',    'icon': '🌀', 'rarity': 'legendary', 'classes': ['siren'], 'max_stacks': 1,
     'desc': 'Charmed humans auto-convert nearby', 'effect': lambda p: setattr(p, 'hypnotic', True)},
]

def generate_upgrade_choices(player_class, wave):
    """Generate 3 random upgrades, weighted by rarity and class match."""
    # Filter upgrades: available (not maxed out - we check this at apply time)
    available = [u for u in UPGRADES if u['classes'] is None or player_class in u['classes']]

    # Weight by rarity + class match bonus
    weighted = []
    for u in available:
        weight = RARITY_WEIGHTS[u['rarity']]
        # Class-specific upgrades get 3x weight
        if u['classes'] is not None and player_class in u['classes']:
            weight *= 3
        # Legendary upgrades more common in later waves
        if u['rarity'] == 'legendary' and wave >= 5:
            weight *= 1.5
        if u['rarity'] == 'epic' and wave >= 3:
            weight *= 1.3
        weighted.append((u, weight))

    # Pick 3 unique upgrades
    choices = []
    attempts = 0
    while len(choices) < 3 and attempts < 50:
        total = sum(w for _, w in weighted)
        r = random.uniform(0, total)
        cumulative = 0
        for u, w in weighted:
            cumulative += w
            if r <= cumulative:
                if u not in choices:
                    choices.append(u)
                break
        attempts += 1

    # Fallback: just pick first 3 if random failed
    while len(choices) < 3:
        for u in available:
            if u not in choices:
                choices.append(u)
                if len(choices) == 3: break

    return choices[:3]

# =====================================================================
# ELITE ENEMY VARIANTS
# =====================================================================
ELITE_VARIANTS = {
    'none':     {'name': 'Normal',    'hp_mult': 1.0, 'speed_mult': 1.0, 'color': (200, 200, 200), 'symbol': '',   'desc': 'Standard enemy'},
    'shielded': {'name': 'Shielded',  'hp_mult': 1.5, 'speed_mult': 0.9, 'color': (100, 150, 255), 'symbol': '🛡️', 'desc': 'Takes reduced damage'},
    'fast':     {'name': 'Fast',      'hp_mult': 0.6, 'speed_mult': 1.8, 'color': (255, 200, 50),  'symbol': '⚡', 'desc': 'Very fast, low HP'},
    'tank':     {'name': 'Tank',      'hp_mult': 2.5, 'speed_mult': 0.7, 'color': (180, 80, 80),   'symbol': '🛡️', 'desc': 'High HP, slow'},
    'bomber':   {'name': 'Bomber',    'hp_mult': 0.8, 'speed_mult': 1.2, 'color': (255, 100, 50),  'symbol': '💣', 'desc': 'Explodes on death'},
}

# =====================================================================
# WAVE ARCHETYPES
# =====================================================================
WAVE_ARCHETYPES = {
    'normal':   {'humans_mult': 1.0, 'enemies_mult': 1.0, 'elite_chance': 0.0, 'golden_mult': 1.0},
    'horde':    {'humans_mult': 1.8, 'enemies_mult': 0.6, 'elite_chance': 0.0, 'golden_mult': 1.5},
    'elite':    {'humans_mult': 0.7, 'enemies_mult': 1.2, 'elite_chance': 0.6, 'golden_mult': 1.0},
    'breather': {'humans_mult': 0.5, 'enemies_mult': 0.3, 'elite_chance': 0.0, 'golden_mult': 2.0},
    'boss':     {'humans_mult': 0.8, 'enemies_mult': 0.5, 'elite_chance': 0.0, 'golden_mult': 1.0},
}

class AdaptiveDifficulty:
    def __init__(self):
        self.heat = 1.0
        self.recent_performance = []
        self.max_history = 5

    def record_wave(self, time_seconds, damage_taken, humans_total, wave_num):
        perf = 1.0
        expected_time = wave_num * 8 + 15
        if time_seconds < expected_time * 0.6: perf += 0.5
        elif time_seconds < expected_time * 0.8: perf += 0.25
        elif time_seconds > expected_time * 1.5: perf -= 0.3
        if damage_taken == 0: perf += 0.5
        elif damage_taken >= 2: perf -= 0.3
        self.recent_performance.append(perf)
        if len(self.recent_performance) > self.max_history:
            self.recent_performance.pop(0)
        avg_perf = sum(self.recent_performance) / len(self.recent_performance)
        self.heat = self.heat * 0.7 + avg_perf * 0.3
        self.heat = max(0.0, min(2.0, self.heat))

    def get_difficulty_mult(self):
        return 0.85 + (self.heat * 0.2)

    def get_golden_bonus(self):
        if self.heat < 0.5: return 1.5
        elif self.heat > 1.5: return 0.7
        return 1.0

    def get_powerup_bonus(self):
        if self.heat < 0.5: return 1.4
        elif self.heat > 1.5: return 0.8
        return 1.0

    def get_heat_label(self):
        if self.heat < 0.4: return ("Chill", (100, 200, 255))
        if self.heat < 0.8: return ("Balanced", (150, 255, 150))
        if self.heat < 1.3: return ("Hot", (255, 200, 100))
        if self.heat < 1.7: return ("Burning", (255, 100, 50))
        return ("INFERNO", (255, 50, 50))

def get_wave_archetype(wave):
    if wave % 10 == 0: return 'boss'
    if wave % 5 == 0: return 'breather'
    if wave % 10 in (3, 7): return 'elite'
    if wave % 10 in (2, 6): return 'horde'
    return 'normal'

def get_wave_config(wave, adaptive_diff=None):
    archetype = get_wave_archetype(wave)
    arch = WAVE_ARCHETYPES[archetype]
    if wave <= 10:
        base_humans = 3 + wave * 0.8
        base_enemies = 1 + wave * 0.4
        hp_mult = 0.7 + wave * 0.13
        speed_mult = 0.8 + wave * 0.05
        backup_mult = 2.0 - wave * 0.11
    else:
        bonus = wave - 10
        base_humans = 10 + min(10, bonus * 0.8)
        base_enemies = 5 + min(5, bonus * 0.4)
        hp_mult = 2.0 + min(3.0, bonus * 0.2)
        speed_mult = 1.3 + min(0.5, bonus * 0.03)
        backup_mult = max(0.5, 0.9 - bonus * 0.03)

    humans = int(base_humans * arch['humans_mult'])
    enemies = int(base_enemies * arch['enemies_mult'])
    elite_chance = arch['elite_chance']
    if wave > 10:
        elite_chance = min(0.8, elite_chance + (wave - 10) * 0.02)
    elite_count = sum(1 for _ in range(enemies) if random.random() < elite_chance)

    golden_chance = 0.2 + wave * 0.02
    if adaptive_diff:
        golden_chance *= adaptive_diff.get_golden_bonus()
    golden_chance *= arch['golden_mult']
    golden_chance = min(0.8, golden_chance)

    adapt_mult = 1.0
    if adaptive_diff:
        adapt_mult = adaptive_diff.get_difficulty_mult()

    return {
        'humans': max(1, humans), 'enemies': max(1, enemies),
        'elite_count': min(elite_count, enemies),
        'hp_mult': hp_mult * adapt_mult, 'speed_mult': speed_mult * adapt_mult,
        'backup_mult': backup_mult, 'golden_chance': golden_chance,
        'archetype': archetype, 'is_boss': (archetype == 'boss'),
    }

DEATH_MESSAGES = [
    "You got ratio'd by a Hunter 📉", "Skill issue detected 💀",
    "The Hunters called, they want their win back",
    "Certified ouch moment", "Your horde has left the chat",
    "Plot twist: you were the weak one", "Achievement unlocked: Get Rekt",
    "The Hunters send their regards", "You've been visited by the L",
    "Error 404: Victory not found",
]

COMBO_MILESTONES = {
    5:  {"text": "NICE! 🔥", "color": (255, 150, 50)},
    10: {"text": "GREAT! 💥", "color": (255, 100, 50)},
    15: {"text": "AMAZING! ⚡", "color": (255, 50, 100)},
    20: {"text": "UNSTOPPABLE! 🌟", "color": (255, 50, 255)},
    25: {"text": "LEGENDARY! 👑", "color": (255, 215, 0)},
}

DIFFICULTY = {
    'easy':   {'enemy_hp_mult': 0.7, 'enemy_speed_mult': 0.8, 'backup_mult': 1.5, 'label': 'EASY',   'score_mult': 0.8},
    'normal': {'enemy_hp_mult': 1.0, 'enemy_speed_mult': 1.0, 'backup_mult': 1.0, 'label': 'NORMAL', 'score_mult': 1.0},
    'hard':   {'enemy_hp_mult': 1.4, 'enemy_speed_mult': 1.2, 'backup_mult': 0.7, 'label': 'HARD',   'score_mult': 1.5}
}
DIFF_LABELS = {'easy': '🟢 EASY', 'normal': '🟡 NORMAL', 'hard': '🔴 HARD'}

NEMESIS_MAP = {
    'vampire':     {'emoji': '1f3f9', 'name': 'Hunter',      'hp': 3, 'speed': 1.5, 'cd': 60},
    'zombie':      {'emoji': '1f52b', 'name': 'Soldier',     'hp': 5, 'speed': 1.2, 'cd': 45},
    'witch':       {'emoji': '1f525', 'name': 'Inquisitor',  'hp': 3, 'speed': 1.4, 'cd': 80},
    'werewolf':    {'emoji': '1faa4', 'name': 'Trapper',     'hp': 3, 'speed': 1.6, 'cd': 90},
    'ghost':       {'emoji': '1f9ea', 'name': 'Ghostbuster', 'hp': 3, 'speed': 1.5, 'cd': 50},
    'alien':       {'emoji': '1f575', 'name': 'Agent',       'hp': 3, 'speed': 1.7, 'cd': 55},
    'shadow':      {'emoji': '1f526', 'name': 'Lightbringer','hp': 3, 'speed': 1.5, 'cd': 60},
    'necromancer': {'emoji': '1f4ff', 'name': 'Priest',      'hp': 4, 'speed': 1.3, 'cd': 70},
    'slime':       {'emoji': '1f9f9', 'name': 'Janitor',     'hp': 3, 'speed': 1.4, 'cd': 50},
    'siren':       {'emoji': '1f9cf', 'name': 'Guard',       'hp': 4, 'speed': 1.5, 'cd': 60}
}

ACHIEVEMENTS = [
    {'id': 'first_blood',    'name': 'First Blood',       'desc': 'Convert your first human',         'icon': '💉'},
    {'id': 'combo_5',        'name': 'Hot Streak',        'desc': 'Reach a 5x combo',                 'icon': '🔥'},
    {'id': 'combo_10',       'name': 'On Fire',           'desc': 'Reach a 10x combo',                'icon': '💥'},
    {'id': 'combo_20',       'name': 'Unstoppable',       'desc': 'Reach a 20x combo',                'icon': '⚡'},
    {'id': 'no_damage',      'name': 'Untouchable',       'desc': 'Complete a wave without damage',   'icon': '🛡️'},
    {'id': 'golden_hunter',  'name': 'Lucky Find',        'desc': 'Convert a Golden Human',           'icon': '✨'},
    {'id': 'critical_master','name': 'Critical Master',   'desc': 'Land 10 critical conversions',     'icon': '💎'},
    {'id': 'horde_15',       'name': 'Army Builder',      'desc': 'Have 15 converted minions at once','icon': '👥'},
    {'id': 'all_classes',    'name': 'Monster Collector', 'desc': 'Win with every class',             'icon': '👑'},
    {'id': 'wave_5',         'name': 'Survivor',          'desc': 'Reach Wave 5',                     'icon': '🌊'},
    {'id': 'wave_10',        'name': 'Champion',          'desc': 'Beat Wave 10',                     'icon': '🏆'},
    {'id': 'wave_20',        'name': 'Endless Legend',    'desc': 'Reach Wave 20',                    'icon': '♾️'},
    {'id': 'boss_slayer',    'name': 'Boss Slayer',       'desc': 'Defeat a Boss',                    'icon': '⚔️'},
    {'id': 'upgrade_legend', 'name': 'Power Hungry',      'desc': 'Collect 3 Legendary upgrades',     'icon': '🌟'},
    {'id': 'full_build',     'name': 'Fully Upgraded',    'desc': 'Have 8+ upgrades at once',         'icon': '⚡'},
]

DATA_FILE = "monster_data.json"

def load_data():
    default = {
        'high_scores': {cls: 0 for cls in NEMESIS_MAP},
        'achievements': [], 'total_wins': 0, 'best_combo': 0, 'best_score': 0, 'best_wave': 0,
        'wins_per_class': {cls: 0 for cls in NEMESIS_MAP},
        'first_run': True, 'daily_best': 0, 'daily_best_wave': 0, 'daily_date': '',
        'total_criticals': 0, 'perfect_wave_streak': 0,
        'total_elites_killed': 0, 'total_bosses_killed': 0, 'total_legendaries': 0,
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data: data[k] = v
                return data
        except: pass
    return default

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

class SpatialGrid:
    def __init__(self, cell_size=60):
        self.cell_size = cell_size; self.grid = {}
    def clear(self): self.grid.clear()
    def insert(self, entity):
        key = (int(entity.x // self.cell_size), int(entity.y // self.cell_size))
        if key not in self.grid: self.grid[key] = []
        self.grid[key].append(entity)
    def get_nearby(self, x, y, radius):
        results = []; cs = self.cell_size
        for cx in range(int((x - radius) // cs), int((x + radius) // cs) + 1):
            for cy in range(int((y - radius) // cs), int((y + radius) // cs) + 1):
                if (cx, cy) in self.grid: results.extend(self.grid[(cx, cy)])
        return results

def dist_sq(x1, y1, x2, y2):
    dx = x1 - x2; dy = y1 - y2
    return dx * dx + dy * dy

def check_collision_sq(e1, e2):
    r = e1.radius + e2.radius
    return dist_sq(e1.x, e1.y, e2.x, e2.y) < r * r

def point_in_radius_sq(px, py, cx, cy, r):
    return dist_sq(px, py, cx, cy) < r * r

class EmojiManager:
    def __init__(self):
        self.cache_dir = ".emoji_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.surfaces = {}; self.scale_cache = {}; self.fallback_mode = False
        self.emoji_map = {
            'vampire': '1f9db', 'zombie': '1f9df', 'witch': '1f9d9',
            'werewolf': '1f43a', 'ghost': '1f47b', 'alien': '1f47d',
            'shadow': '1f977', 'necromancer': '1f480', 'slime': '1f7e2',
            'siren': '1f9dc', 'human': '1f9d1', 'tombstone': '1faa6',
            'droplet': '1f4a7', 'sparkle': '2728', 'heart': '2764',
            'lightning': '26a1', 'boom': '1f4a5', 'shield': '1f6e1',
            'clock': '23f0', 'gem': '1f48e', 'star': '2b50',
            'crown': '1f451', 'trophy': '1f3c6', 'wave': '1f30a'
        }
        for cls, data in NEMESIS_MAP.items():
            self.emoji_map[f"enemy_{cls}"] = data['emoji']
        print("Loading emojis...")
        for name, code in self.emoji_map.items():
            path = os.path.join(self.cache_dir, f"{code}.png")
            if not os.path.exists(path):
                url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{code}.png"
                try: urllib.request.urlretrieve(url, path)
                except: self.fallback_mode = True; break
            if os.path.exists(path):
                try: self.surfaces[name] = pygame.image.load(path).convert_alpha()
                except: self.fallback_mode = True

    def get(self, name, size):
        key = (name, size)
        if key in self.scale_cache: return self.scale_cache[key]
        if name in self.surfaces:
            scaled = pygame.transform.smoothscale(self.surfaces[name], (size, size))
            self.scale_cache[key] = scaled
            return scaled
        return None

_font_cache = {}
_text_cache = {}

def draw_text(screen, text, size, x, y, color=WHITE, center=False):
    cache_key = (text, size, color)
    if cache_key in _text_cache:
        img = _text_cache[cache_key]
    else:
        if len(_text_cache) > 800: _text_cache.clear()
        if size not in _font_cache:
            _font_cache[size] = pygame.font.SysFont("Arial", size, bold=True)
        img = _font_cache[size].render(text, True, color)
        _text_cache[cache_key] = img
    rect = img.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(img, rect)

class FloatingNumber:
    __slots__ = ['x', 'y', 'text', 'color', 'life', 'max_life', 'vy', 'size', 'active']
    def __init__(self): self.active = False
    def init(self, x, y, text, color, size=24):
        self.x = x + random.uniform(-10, 10); self.y = y
        self.text = text; self.color = color; self.size = size
        self.life = 60; self.max_life = 60; self.vy = -2.5; self.active = True
    def update(self):
        if not self.active: return False
        self.y += self.vy; self.vy *= 0.95; self.life -= 1
        if self.life <= 0: self.active = False; return False
        return True
    def draw(self, screen):
        if not self.active: return
        c = tuple(max(0, int(v * (self.life / self.max_life))) for v in self.color)
        draw_text(screen, self.text, self.size, int(self.x), int(self.y), c, center=True)

class FloatingNumberPool:
    def __init__(self, size=100):
        self.pool = [FloatingNumber() for _ in range(size)]; self.active = []
    def spawn(self, x, y, text, color, size=24):
        for p in self.pool:
            if not p.active:
                p.init(x, y, text, color, size); self.active.append(p); return
        p = FloatingNumber(); p.init(x, y, text, color, size)
        self.pool.append(p); self.active.append(p)
    def update_all(self):
        new_active = []
        for p in self.active:
            if p.update(): new_active.append(p)
        self.active = new_active
    def draw_all(self, screen):
        for p in self.active: p.draw(screen)

class WaveAnnouncer:
    def __init__(self):
        self.text = ""; self.sub_text = ""; self.color = WHITE
        self.timer = 0; self.max_timer = 120; self.scale = 1.0
    def trigger(self, wave, cfg):
        if cfg['is_boss']:
            self.text = f"⚔️ BOSS WAVE {wave} ⚔️"; self.sub_text = "Prepare yourself!"
            self.color = (255, 50, 50); self.max_timer = 180
        elif wave > 10:
            self.text = f"🌊 WAVE {wave} 🌊"; self.sub_text = f"ENDLESS - {cfg['archetype'].upper()}"
            self.color = (150, 100, 255); self.max_timer = 120
        else:
            self.text = f"🌊 WAVE {wave} 🌊"
            arch_desc = {'normal': f"{cfg['humans']} humans", 'horde': f"HORDE! {cfg['humans']} humans!",
                        'elite': "ELITE SQUAD!", 'breather': "Breather wave"}
            self.sub_text = arch_desc.get(cfg['archetype'], f"{cfg['humans']} humans")
            self.color = GOLD; self.max_timer = 120
        self.timer = self.max_timer; self.scale = 2.5
    def update(self):
        if self.timer > 0:
            self.timer -= 1
            if self.timer > self.max_timer - 20:
                progress = (self.max_timer - self.timer) / 20
                self.scale = 2.5 - progress * 1.5
            else: self.scale = 1.0
    def draw(self, screen):
        if self.timer <= 0: return
        alpha = self.timer / 30 if self.timer < 30 else 1.0
        if self.timer > self.max_timer - 15:
            flash_alpha = int(80 * (1 - (self.max_timer - self.timer) / 15))
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*self.color, flash_alpha)); screen.blit(flash_surf, (0, 0))
        size = int(72 * self.scale)
        c = tuple(int(v * alpha) for v in self.color)
        draw_text(screen, self.text, size, WIDTH//2, HEIGHT//2 - 40, c, center=True)
        if self.sub_text:
            sub_size = int(24 * min(1.0, self.scale))
            sub_c = tuple(int(v * alpha * 0.8) for v in WHITE)
            draw_text(screen, self.sub_text, sub_size, WIDTH//2, HEIGHT//2 + 30, sub_c, center=True)

class WaveCompletePopup:
    def __init__(self):
        self.wave = 0; self.timer = 0; self.max_timer = 180
        self.reward_text = ""; self.is_endless_unlock = False; self.archetype = 'normal'
    def trigger(self, wave, reward_text, is_endless_unlock=False, archetype='normal'):
        self.wave = wave; self.timer = self.max_timer; self.reward_text = reward_text
        self.is_endless_unlock = is_endless_unlock; self.archetype = archetype
    def update(self):
        if self.timer > 0: self.timer -= 1
    def draw(self, screen):
        if self.timer <= 0: return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(150, int(150 * (self.timer / self.max_timer)))))
        screen.blit(overlay, (0, 0))
        if self.is_endless_unlock:
            draw_text(screen, "🏆 MAIN GAME COMPLETE! 🏆", 48, WIDTH//2, HEIGHT//2 - 80, GOLD, center=True)
            draw_text(screen, "ENDLESS MODE UNLOCKED!", 32, WIDTH//2, HEIGHT//2 - 30, (150, 100, 255), center=True)
        else:
            draw_text(screen, f"✅ WAVE {self.wave} COMPLETE!", 44, WIDTH//2, HEIGHT//2 - 60, GOLD, center=True)
        draw_text(screen, self.reward_text, 24, WIDTH//2, HEIGHT//2 + 20, (100, 255, 100), center=True)
        draw_text(screen, "Choose your upgrade!", 22, WIDTH//2, HEIGHT//2 + 60, (255, 220, 100), center=True)

class AchievementPopup:
    def __init__(self):
        self.queue = []; self.current = None; self.timer = 0
    def trigger(self, achievement): self.queue.append(achievement)
    def update(self):
        if self.current is None:
            if self.queue: self.current = self.queue.pop(0); self.timer = 180
        else:
            self.timer -= 1
            if self.timer <= 0: self.current = None
    def draw(self, screen):
        if self.current is None: return
        progress = min(1.0, (180 - self.timer) / 20) if self.timer > 160 else (1.0 if self.timer > 20 else self.timer / 20)
        y = int(-80 + progress * 100)
        popup_surf = pygame.Surface((400, 70), pygame.SRCALPHA)
        popup_surf.fill((20, 20, 30, 220))
        pygame.draw.rect(popup_surf, GOLD, (0, 0, 400, 70), 3)
        screen.blit(popup_surf, (WIDTH//2 - 200, y))
        draw_text(screen, f"{self.current['icon']} ACHIEVEMENT UNLOCKED!", 18, WIDTH//2, y + 20, GOLD, center=True)
        draw_text(screen, f"{self.current['name']} - {self.current['desc']}", 16, WIDTH//2, y + 45, WHITE, center=True)

class HitStop:
    def __init__(self): self.frames = 0
    def trigger(self, frames=6): self.frames = max(self.frames, frames)
    def update(self):
        if self.frames > 0: self.frames -= 1; return True
        return False

class ComboFlash:
    def __init__(self):
        self.text = ""; self.color = WHITE; self.timer = 0; self.scale = 1.0
    def trigger(self, text, color):
        self.text = text; self.color = color; self.timer = 90; self.scale = 2.0
    def update(self):
        if self.timer > 0: self.timer -= 1; self.scale = max(1.0, self.scale * 0.95)
    def draw(self, screen):
        if self.timer <= 0: return
        alpha = min(255, self.timer * 4); size = int(64 * self.scale)
        c = tuple(int(v * (alpha / 255)) for v in self.color)
        draw_text(screen, self.text, size, WIDTH//2, HEIGHT//2 - 50, c, center=True)

class Particle:
    __slots__ = ['x', 'y', 'color', 'vx', 'vy', 'life', 'max_life', 'size', 'gravity', 'active']
    def __init__(self): self.active = False
    def init(self, x, y, color, p_type='sparkle'):
        self.x = x; self.y = y; self.color = color
        angle = random.uniform(0, PI_2)
        speed = random.uniform(1, 4) if p_type != 'smoke' else random.uniform(0.3, 1)
        self.vx = math.cos(angle) * speed; self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 45) if p_type != 'smoke' else random.randint(30, 60)
        self.max_life = self.life
        self.size = random.randint(2, 5) if p_type != 'smoke' else random.randint(4, 8)
        self.gravity = 0.1 if p_type == 'blood' else 0; self.active = True
    def update(self):
        if not self.active: return False
        self.x += self.vx; self.y += self.vy; self.vy += self.gravity
        self.vx *= 0.96; self.vy *= 0.96; self.life -= 1
        if self.life <= 0: self.active = False; return False
        return True
    def draw(self, screen):
        if not self.active: return
        size = int(self.size * (self.life / self.max_life))
        if size < 1: return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class ParticlePool:
    def __init__(self, initial_size=300):
        self.pool = [Particle() for _ in range(initial_size)]; self.active = []
    def spawn(self, x, y, color, count=8, p_type='sparkle'):
        for _ in range(count):
            particle = None
            for p in self.pool:
                if not p.active: particle = p; break
            if particle is None:
                particle = Particle(); self.pool.append(particle)
            particle.init(x, y, color, p_type); self.active.append(particle)
    def update_all(self):
        new_active = []
        for p in self.active:
            if p.update(): new_active.append(p)
        self.active = new_active
    def draw_all(self, screen):
        for p in self.active: p.draw(screen)

def create_background_surface():
    bg = pygame.Surface((WIDTH + 80, HEIGHT + 80)); bg.fill(BG_COLOR)
    for x in range(0, WIDTH + 80, 40): pygame.draw.line(bg, (40, 40, 45), (x, 0), (x, HEIGHT + 80), 1)
    for y in range(0, HEIGHT + 80, 40): pygame.draw.line(bg, (40, 40, 45), (0, y), (WIDTH + 80, y), 1)
    return bg

_aura_cache = {}
def get_aura_surface(color, radius):
    key = (color, radius)
    if key in _aura_cache: return _aura_cache[key]
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, 40), (radius, radius), radius)
    _aura_cache[key] = surf; return surf

_shield_cache = {}
def get_shield_surface(size):
    if size in _shield_cache: return _shield_cache[size]
    surf = pygame.Surface((size + 12, size + 12), pygame.SRCALPHA)
    pygame.draw.circle(surf, (100, 200, 255, 100), (size // 2 + 6, size // 2 + 6), size // 2 + 4, 3)
    _shield_cache[size] = surf; return surf

_glow_cache = {}
def get_glow_surface(color, radius):
    key = (color, radius)
    if key in _glow_cache: return _glow_cache[key]
    size = radius * 2 + 10
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, 100), (size // 2, size // 2), radius + 3)
    _glow_cache[key] = surf; return surf

_overlay_cache = {}
def get_overlay_surface(color, alpha):
    key = (color, alpha)
    if key in _overlay_cache: return _overlay_cache[key]
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    surf.fill((*color, alpha)); _overlay_cache[key] = surf; return surf

_heart_cache = {}
def get_heart_surface(emoji_mgr, alpha=255):
    if alpha in _heart_cache: return _heart_cache[alpha]
    heart = emoji_mgr.get('heart', 24)
    if heart:
        if alpha < 255: heart = heart.copy(); heart.set_alpha(alpha)
        _heart_cache[alpha] = heart; return heart
    return None

def get_daily_seed():
    today = time.strftime("%Y-%m-%d")
    return int(hashlib.md5(today.encode()).hexdigest()[:8], 16)

POWERUP_TYPES = [
    {'name': 'health',     'emoji': 'heart',     'color': (255, 80, 80),   'duration': 0},
    {'name': 'speed',      'emoji': 'lightning',  'color': (255, 220, 50),  'duration': 600},
    {'name': 'damage',     'emoji': 'boom',       'color': (255, 100, 50),  'duration': 600},
    {'name': 'shield',     'emoji': 'shield',     'color': (100, 200, 255), 'duration': 0},
    {'name': 'slowmo',     'emoji': 'clock',      'color': (200, 150, 255), 'duration': 360},
    {'name': 'multiplier', 'emoji': 'gem',        'color': (150, 255, 200), 'duration': 480}
]

class PowerUp:
    __slots__ = ['x', 'y', 'data', 'emoji_mgr', 'radius', 'life', 'bob_offset']
    def __init__(self, x, y, p_type_data, emoji_mgr):
        self.x = x; self.y = y; self.data = p_type_data
        self.emoji_mgr = emoji_mgr; self.radius = 16
        self.life = 600; self.bob_offset = random.uniform(0, PI_2)
    def update(self):
        self.life -= 1; self.bob_offset += 0.1; return self.life > 0
    def draw(self, screen):
        bob = math.sin(self.bob_offset) * 4; size = self.radius * 2
        glow = get_glow_surface(self.data['color'], self.radius)
        screen.blit(glow, (int(self.x) - size // 2 - 5, int(self.y) - size // 2 - 5 + int(bob)))
        img = self.emoji_mgr.get(self.data['emoji'], size)
        if img: screen.blit(img, (int(self.x) - self.radius, int(self.y) - self.radius + int(bob)))
        else: pygame.draw.circle(screen, self.data['color'], (int(self.x), int(self.y) + int(bob)), self.radius)

class Player:
    def __init__(self, char_class, emoji_mgr, difficulty):
        self.x = WIDTH // 2; self.y = HEIGHT // 2
        self.char_class = char_class; self.emoji_mgr = emoji_mgr; self.emoji_name = char_class
        self.hp = 3; self.max_hp = 3; self.iframes = 0
        self.base_speed = 0; self.speed = 0
        self.shield = False
        self.buffs = {'speed': 0, 'damage': 0, 'slowmo': 0, 'multiplier': 0}
        self.difficulty = difficulty
        # Upgrade-related attributes (defaults)
        self.bump_damage = 1
        self.crit_bonus = 0.0
        self.iframe_bonus = 0
        self.iframe_mult = 1.0
        self.vampiric = False
        self.golden_bonus = 0.0
        self.power_duration_mult = 1.0
        self.combo_timer_mult = 1.0
        self.score_mult = 1.0
        self.berserker = False
        self.second_wind = False
        self.second_wind_used = False
        self.magnet = False
        self.chrono_start = False
        self.blood_frenzy = False
        self.minion_speed_mult = 1.0
        self.regen = False
        self.regen_timer = 0
        self.minion_aura = 0
        self.frenzy_mult = 1.0
        self.howl_dash = False
        self.howl_cd = 0
        self.trail_life_mult = 1.0
        self.trail_damage = 0
        self.trail_width_mult = 1.0
        self.beam_cd_mult = 1.0
        self.beam_aoe = 0
        self.orbital_strike = False
        self.dash_cd_mult = 1.0
        self.shadow_clone = False
        self.dash_distance = 120
        self.max_graves = 3
        self.grave_range = 36
        self.phylactery = False
        self.phylactery_used = False
        self.puddle_size_mult = 1.0
        self.puddle_damage = 0
        self.split_on_hit = False
        self.charm_duration_mult = 1.0
        self.charm_damage = False
        self.hypnotic = False
        self.spell_echo = False
        self.spell_echo_timer = 0
        self.upgrades = []  # List of owned upgrade IDs
        self.conversions_since_heal = 0  # For vampiric

        stats = {
            'vampire':     ((200,30,30),   4.5, 18, 0),
            'zombie':      ((30,160,30),   2.5, 26, 0),
            'witch':       ((160,30,160),  3.5, 18, 65),
            'werewolf':    ((220,120,30),  3.0, 20, 0),
            'ghost':       ((150,220,255), 3.2, 16, 0),
            'alien':       ((50,255,50),   3.0, 18, 0),
            'shadow':      ((60,0,90),     3.5, 16, 0),
            'necromancer': ((120,120,130), 2.8, 18, 0),
            'slime':       ((180,220,50),  2.2, 22, 0),
            'siren':       ((255,100,150), 3.0, 18, 0),
        }
        c, s, r, a = stats[char_class]
        self.color = c; self.speed = s; self.base_speed = s; self.radius = r; self.aura = a
        self.trail = []; self.rays = []; self.ray_cooldown = 0
        self.teleport_cd = 0; self.last_dir = (1, 0)
        self.graves = []; self.grave_cd = 0
        self.puddles = []; self.puddle_timer = 0
        self.charm_cd = 0; self.charm_active = 0

    def apply_upgrade(self, upgrade):
        """Apply an upgrade to the player."""
        upgrade['effect'](self)
        self.upgrades.append(upgrade['id'])

    def count_upgrade(self, upgrade_id):
        """Count how many times an upgrade has been taken."""
        return self.upgrades.count(upgrade_id)

    def update(self, keys):
        moved = False
        eff = self.base_speed * (1.5 if self.buffs['speed'] > 0 else 1.0)
        if self.berserker and self.hp < self.max_hp * 0.5:
            eff *= 1.3
        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.y -= eff; moved = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:   self.y += eff; moved = True
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:   self.x -= eff; moved = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  self.x += eff; moved = True
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        if self.iframes > 0: self.iframes -= 1
        for b in self.buffs:
            if self.buffs[b] > 0: self.buffs[b] -= 1

        # Regen upgrade
        if self.regen:
            self.regen_timer += 1
            if self.regen_timer >= 900 and self.hp < self.max_hp:  # 15 seconds
                self.hp += 1; self.regen_timer = 0

        # Spell echo (witch)
        if self.spell_echo and self.aura > 0:
            self.spell_echo_timer += 1
            if self.spell_echo_timer >= 120:  # 2 seconds
                self.spell_echo_timer = 0
                # Will be handled in main loop

        # Werewolf howl dash
        if self.howl_dash and self.howl_cd > 0: self.howl_cd -= 1

        if self.char_class == 'ghost':
            trail_life = int(60 * self.trail_life_mult)
            if moved: self.trail.append((self.x, self.y, trail_life))
            self.trail = [(t[0], t[1], t[2]-1) for t in self.trail if t[2] > 1]
        if self.char_class == 'alien' and self.ray_cooldown > 0: self.ray_cooldown -= 1
        if self.char_class == 'shadow':
            if moved:
                dx = dy = 0
                if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
                if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
                if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
                if dx or dy:
                    mag = math.hypot(dx, dy); self.last_dir = (dx/mag, dy/mag)
            if self.teleport_cd > 0: self.teleport_cd -= 1
        if self.char_class == 'necromancer' and self.grave_cd > 0: self.grave_cd -= 1
        if self.char_class == 'slime':
            if moved:
                self.puddle_timer += 1
                if self.puddle_timer >= 8:
                    p_size = int(18 * self.puddle_size_mult)
                    self.puddles.append([self.x, self.y, 300, p_size]); self.puddle_timer = 0
            self.puddles = [[p[0], p[1], p[2]-1, p[3]] for p in self.puddles if p[2] > 1]
        if self.char_class == 'siren':
            if self.charm_cd > 0: self.charm_cd -= 1
            if self.charm_active > 0: self.charm_active -= 1

    def draw(self, screen):
        if self.aura > 0:
            screen.blit(get_aura_surface(self.color, self.aura), (self.x - self.aura, self.y - self.aura))
        if self.char_class == 'ghost':
            for t in self.trail:
                r = t[2] / (60 * self.trail_life_mult)
                base_size = int(self.radius * 1.5 * self.trail_width_mult)
                size = int(base_size * r)
                if size > 0:
                    c = tuple(int(v * r) for v in self.color)
                    pygame.draw.circle(screen, c, (int(t[0]), int(t[1])), size)
        if self.char_class == 'alien':
            for r in self.rays:
                img = self.emoji_mgr.get('sparkle', 16)
                if img: screen.blit(img, (r[0] - 8, r[1] - 8))
                else: pygame.draw.circle(screen, (200, 255, 200), (int(r[0]), int(r[1])), 6)
        if self.char_class == 'necromancer':
            for g in self.graves:
                img = self.emoji_mgr.get('tombstone', 36)
                if img: screen.blit(img, (g[0] - 18, g[1] - 18))
                else: pygame.draw.rect(screen, (80, 80, 90), (g[0]-15, g[1]-15, 30, 30))
        if self.char_class == 'slime':
            for p in self.puddles:
                r = p[2] / 300
                size = int(p[3] * r)
                if size > 0:
                    c = tuple(int(v * r) for v in self.color)
                    pygame.draw.circle(screen, c, (int(p[0]), int(p[1])), size)
        if self.iframes > 0 and self.iframes % 10 < 5: return
        size = self.radius * 2
        player_img = self.emoji_mgr.get(self.emoji_name, size)
        if player_img: screen.blit(player_img, (self.x - self.radius, self.y - self.radius))
        else: pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        if self.shield:
            screen.blit(get_shield_surface(size), (self.x - self.radius - 6, self.y - self.radius - 6))

class Villager:
    __slots__ = ['x', 'y', 'radius', 'base_speed', 'color', 'converted', 'alive',
                 'target_x', 'target_y', 'emoji_mgr', 'converted_to', 'converted_color', 'is_golden']
    def __init__(self, x, y, emoji_mgr, is_golden=False):
        self.x = x; self.y = y; self.radius = 14; self.base_speed = 1.5
        self.color = GOLD if is_golden else HUMAN_COLOR
        self.converted = False; self.alive = True
        self.target_x = random.randint(0, WIDTH); self.target_y = random.randint(0, HEIGHT)
        self.emoji_mgr = emoji_mgr
        self.converted_to = ''; self.converted_color = HUMAN_COLOR
        self.is_golden = is_golden
    def update(self, converted_list, enemies, player, player_class, charm_active, minion_speed_mult=1.0):
        if not self.alive: return
        if not self.converted:
            if charm_active > 0 and player_class != 'siren': return
            dx = self.target_x - self.x; dy = self.target_y - self.y
            d = dx * dx + dy * dy
            if d < 25:
                self.target_x = random.randint(0, WIDTH); self.target_y = random.randint(0, HEIGHT)
            else:
                dist = math.sqrt(d)
                self.x += (dx / dist) * self.base_speed; self.y += (dy / dist) * self.base_speed
        else:
            target = None; min_d = float('inf')
            for v in converted_list:
                d = dist_sq(v.x, v.y, self.x, self.y)
                if d < min_d: min_d = d; target = v
            for e in enemies:
                d = dist_sq(e.x, e.y, self.x, self.y)
                if d < 22500 and d < min_d: min_d = d; target = e
            if target is None:
                d = dist_sq(player.x, player.y, self.x, self.y)
                if d > 3600:
                    dx = player.x - self.x; dy = player.y - self.y
                    dist = math.sqrt(d)
                    self.x += (dx / dist) * (self.base_speed * 1.1 * minion_speed_mult)
                    self.y += (dy / dist) * (self.base_speed * 1.1 * minion_speed_mult)
            else:
                dx = target.x - self.x; dy = target.y - self.y
                d = dx * dx + dy * dy
                if d > 0:
                    dist = math.sqrt(d)
                    self.x += (dx / dist) * (self.base_speed * 1.3 * minion_speed_mult)
                    self.y += (dy / dist) * (self.base_speed * 1.3 * minion_speed_mult)
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
    def draw(self, screen):
        if not self.alive: return
        size = self.radius * 2
        if self.converted: img = self.emoji_mgr.get(self.converted_to, size)
        else: img = self.emoji_mgr.get('human', size)
        if img: screen.blit(img, (self.x - self.radius, self.y - self.radius))
        else: pygame.draw.circle(screen, self.color if not self.converted else self.converted_color, (int(self.x), int(self.y)), self.radius)
        if self.is_golden and not self.converted:
            crown = self.emoji_mgr.get('crown', 16)
            if crown: screen.blit(crown, (int(self.x) - 8, int(self.y) - self.radius - 10))

class Enemy:
    __slots__ = ['x', 'y', 'type', 'emoji_mgr', 'radius', 'speed', 'hp', 'max_hp',
                 'attack_cd', 'max_cd', 'color', 'backup_cd', 'calling_backup', 'difficulty',
                 'wave_hp_mult', 'wave_speed_mult', 'wave_backup_mult',
                 'elite_type', 'is_boss', 'boss_phase', 'boss_attack_cd',
                 'dash_cd', 'dash_dx', 'dash_dy', 'dash_timer']
    def __init__(self, x, y, nemesis_type, emoji_mgr, difficulty,
                 wave_hp_mult=1.0, wave_speed_mult=1.0, wave_backup_mult=1.0,
                 elite_type='none', is_boss=False):
        self.x = x; self.y = y; self.type = nemesis_type; self.emoji_mgr = emoji_mgr
        self.elite_type = elite_type; self.is_boss = is_boss
        self.boss_phase = 1; self.boss_attack_cd = 0
        self.dash_cd = 0; self.dash_dx = 0; self.dash_dy = 0; self.dash_timer = 0
        elite = ELITE_VARIANTS[elite_type]
        diff = DIFFICULTY[difficulty]
        boss_mult = 5.0 if is_boss else 1.0
        boss_radius_mult = 1.8 if is_boss else 1.0
        self.radius = int(18 * boss_radius_mult)
        self.color = elite['color'] if not is_boss else (200, 30, 30)
        self.wave_hp_mult = wave_hp_mult; self.wave_speed_mult = wave_speed_mult
        self.wave_backup_mult = wave_backup_mult
        base_hp = NEMESIS_MAP[nemesis_type]['hp']
        base_speed = NEMESIS_MAP[nemesis_type]['speed']
        self.speed = base_speed * diff['enemy_speed_mult'] * wave_speed_mult * elite['speed_mult']
        self.hp = max(1, int(base_hp * diff['enemy_hp_mult'] * wave_hp_mult * elite['hp_mult'] * boss_mult))
        self.max_hp = self.hp
        self.attack_cd = random.randint(0, NEMESIS_MAP[nemesis_type]['cd'])
        self.max_cd = NEMESIS_MAP[nemesis_type]['cd']
        self.backup_cd = int(random.randint(300, 600) * diff['backup_mult'] * wave_backup_mult)
        self.calling_backup = 0; self.difficulty = difficulty
        if is_boss: self.backup_cd = 99999

    def take_damage(self, amount):
        if self.elite_type == 'shielded': amount = max(1, amount // 2)
        self.hp -= amount
        return self.hp <= 0

    def update(self, player, converted_minions, enemy_bullets, enemy_traps, enemies_list, particle_pool=None, floating_numbers=None):
        if self.is_boss and self.dash_timer > 0:
            self.dash_timer -= 1
            self.x += self.dash_dx * 6; self.y += self.dash_dy * 6
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))
            self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
            if particle_pool: particle_pool.spawn(self.x, self.y, (255, 50, 50), 2, 'smoke')
        else:
            target_x, target_y = player.x, player.y
            min_d = dist_sq(player.x, player.y, self.x, self.y)
            for v in converted_minions:
                d = dist_sq(v.x, v.y, self.x, self.y)
                if d < min_d: min_d = d; target_x, target_y = v.x, v.y
            dx = target_x - self.x; dy = target_y - self.y; d = dx * dx + dy * dy
            if d > 1600:
                dist = math.sqrt(d)
                self.x += (dx / dist) * self.speed; self.y += (dy / dist) * self.speed
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))
            self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        self.attack_cd -= 1
        if self.dash_cd > 0: self.dash_cd -= 1

        if self.is_boss:
            self.boss_attack_cd -= 1
            hp_pct = self.hp / self.max_hp
            if hp_pct < 0.33 and self.boss_phase < 3:
                self.boss_phase = 3; self.speed *= 1.3
            elif hp_pct < 0.66 and self.boss_phase < 2:
                self.boss_phase = 2; self.speed *= 1.15
            if self.boss_attack_cd <= 0 and d < 40000:
                if self.boss_phase == 1:
                    self.boss_attack_cd = 90
                    dist = math.sqrt(d) if d > 0 else 1; angle = math.atan2(dy, dx)
                    enemy_bullets.append([self.x, self.y, math.cos(angle)*6, math.sin(angle)*6, self.type, 180])
                elif self.boss_phase == 2:
                    self.boss_attack_cd = 75; angle = math.atan2(dy, dx)
                    for offset in (-0.3, 0, 0.3):
                        a = angle + offset
                        enemy_bullets.append([self.x, self.y, math.cos(a)*5, math.sin(a)*5, self.type, 150])
                else:
                    self.boss_attack_cd = 100
                    if self.dash_cd == 0 and d > 4000:
                        dist = math.sqrt(d); self.dash_dx = dx / dist; self.dash_dy = dy / dist
                        self.dash_timer = 15; self.dash_cd = 180
                    for i in range(8):
                        a = (i / 8) * PI_2
                        enemy_bullets.append([self.x, self.y, math.cos(a)*4, math.sin(a)*4, self.type, 120])
        else:
            if self.attack_cd <= 0 and d < 90000:
                self.attack_cd = self.max_cd
                dist = math.sqrt(d) if d > 0 else 1
                if self.type == 'werewolf':
                    enemy_traps.append([self.x, self.y, 600, 20])
                else:
                    spd = 5 if self.type != 'witch' else 3
                    enemy_bullets.append([self.x, self.y, (dx/dist)*spd, (dy/dist)*spd, self.type, 120])

        if not self.is_boss:
            self.backup_cd -= 1
            if self.backup_cd <= 0 and len(enemies_list) < MAX_ENEMIES:
                self.calling_backup = 60
                for _ in range(random.randint(1, 2)):
                    if len(enemies_list) < MAX_ENEMIES:
                        enemies_list.append(Enemy(random.choice([50, WIDTH-50]), random.choice([50, HEIGHT-50]),
                                                 self.type, self.emoji_mgr, self.difficulty,
                                                 self.wave_hp_mult, self.wave_speed_mult, self.wave_backup_mult,
                                                 'none', False))
                self.backup_cd = int(random.randint(600, 900) * DIFFICULTY[self.difficulty]['backup_mult'] * self.wave_backup_mult)
            if self.calling_backup > 0: self.calling_backup -= 1

    def draw(self, screen):
        size = self.radius * 2
        if self.is_boss:
            pulse = int(5 + math.sin(pygame.time.get_ticks() * 0.01) * 3)
            aura_color = [(255, 50, 50), (255, 150, 50), (255, 50, 150)][self.boss_phase - 1]
            aura_surf = pygame.Surface((size + pulse*4, size + pulse*4), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (*aura_color, 80), (size//2 + pulse*2, size//2 + pulse*2), size//2 + pulse*2)
            screen.blit(aura_surf, (int(self.x) - self.radius - pulse*2, int(self.y) - self.radius - pulse*2))
        if self.elite_type != 'none' and not self.is_boss:
            ring_surf = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*self.color, 150), (size//2 + 4, size//2 + 4), size//2 + 2, 2)
            screen.blit(ring_surf, (int(self.x) - self.radius - 4, int(self.y) - self.radius - 4))
        img = self.emoji_mgr.get(f"enemy_{self.type}", size)
        if img: screen.blit(img, (self.x - self.radius, self.y - self.radius))
        else: pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        if self.elite_type != 'none' and not self.is_boss:
            sym = ELITE_VARIANTS[self.elite_type]['symbol']
            if sym: draw_text(screen, sym, 14, int(self.x), int(self.y) - self.radius - 18, self.color, center=True)
        if self.is_boss:
            phase_colors = [(255, 100, 100), (255, 200, 50), (255, 50, 200)]
            draw_text(screen, f"P{self.boss_phase}", 16, int(self.x), int(self.y) - self.radius - 18,
                     phase_colors[self.boss_phase - 1], center=True)
        if self.calling_backup > 0:
            pr = self.radius + 5 + (60 - self.calling_backup) // 3
            pygame.draw.circle(screen, (255, 50, 50), (int(self.x), int(self.y)), pr, 3)
        bw = 40 if self.is_boss else 30
        ratio = self.hp / self.max_hp
        bx = self.x - bw // 2; by = self.y - self.radius - 10
        pygame.draw.rect(screen, RED, (bx, by, bw, 4))
        pygame.draw.rect(screen, (50, 200, 50), (bx, by, int(bw * ratio), 4))

def draw_offscreen_indicators(screen, player, enemies):
    px, py = player.x, player.y
    hw, hh = WIDTH // 2, HEIGHT // 2
    for e in enemies:
        if 0 <= e.x <= WIDTH and 0 <= e.y <= HEIGHT: continue
        angle = math.atan2(e.y - py, e.x - px)
        ix = max(20, min(WIDTH - 20, hw + math.cos(angle) * (hw - 40)))
        iy = max(20, min(HEIGHT - 20, hh + math.sin(angle) * (hh - 40)))
        cs, sn = math.cos(angle), math.sin(angle)
        pts = [
            (ix + cs * 10, iy + sn * 10),
            (ix + math.cos(angle + 2.5) * 10, iy + math.sin(angle + 2.5) * 10),
            (ix + math.cos(angle - 2.5) * 10, iy + math.sin(angle - 2.5) * 10)
        ]
        color = (255, 50, 50) if e.is_boss else ((255, 200, 50) if e.elite_type != 'none' else (255, 80, 80))
        pygame.draw.polygon(screen, color, pts)

def check_achievements(data, stats):
    newly_earned = []
    for ach in ACHIEVEMENTS:
        if ach['id'] in data['achievements']: continue
        earned = False
        if ach['id'] == 'first_blood' and stats.get('conversions', 0) >= 1: earned = True
        elif ach['id'] == 'combo_5' and stats.get('max_combo', 0) >= 5: earned = True
        elif ach['id'] == 'combo_10' and stats.get('max_combo', 0) >= 10: earned = True
        elif ach['id'] == 'combo_20' and stats.get('max_combo', 0) >= 20: earned = True
        elif ach['id'] == 'no_damage' and stats.get('wave_no_damage', False): earned = True
        elif ach['id'] == 'golden_hunter' and stats.get('golden_converted', 0) >= 1: earned = True
        elif ach['id'] == 'critical_master' and data.get('total_criticals', 0) + stats.get('criticals', 0) >= 10: earned = True
        elif ach['id'] == 'horde_15' and stats.get('max_horde', 0) >= 15: earned = True
        elif ach['id'] == 'all_classes':
            all_won = all(data['wins_per_class'].get(c, 0) > 0 for c in NEMESIS_MAP)
            if all_won: earned = True
        elif ach['id'] == 'wave_5' and data.get('best_wave', 0) >= 5: earned = True
        elif ach['id'] == 'wave_10' and data.get('best_wave', 0) >= 10: earned = True
        elif ach['id'] == 'wave_20' and data.get('best_wave', 0) >= 20: earned = True
        elif ach['id'] == 'boss_slayer' and data.get('total_bosses_killed', 0) >= 1: earned = True
        elif ach['id'] == 'upgrade_legend' and data.get('total_legendaries', 0) >= 3: earned = True
        elif ach['id'] == 'full_build' and stats.get('upgrade_count', 0) >= 8: earned = True
        if earned:
            data['achievements'].append(ach['id'])
            newly_earned.append(ach)
    return newly_earned

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🎃 Monster Infection - UPGRADE EDITION ⬆️")
    clock = pygame.time.Clock()
    emoji_mgr = EmojiManager()
    bg_surface = create_background_surface()
    spatial_grid = SpatialGrid(cell_size=60)
    particle_pool = ParticlePool(300)
    floating_numbers = FloatingNumberPool(100)
    achievement_popup = AchievementPopup()
    hit_stop = HitStop()
    combo_flash = ComboFlash()
    wave_announcer = WaveAnnouncer()
    wave_complete_popup = WaveCompletePopup()
    adaptive_diff = AdaptiveDifficulty()

    data = load_data()

    state = STATE_MENU
    if data['first_run']:
        state = STATE_TUTORIAL
        data['first_run'] = False
        save_data(data)

    player = None; villagers = []; enemies = []
    enemy_bullets = []; enemy_traps = []; powerups = []
    selected_class = 'vampire'; selected_difficulty = 'normal'
    score = 0; combo = 0; combo_timer = 0; best_combo = 0
    time_counter = 0; powerup_spawn_timer = 300; slowmo_active = 0
    run_stats = {}
    death_message = ""
    new_best = False
    daily_mode = False

    current_wave = 1
    wave_humans_total = 0
    wave_humans_converted = 0
    wave_start_time = 0
    wave_damage_taken = 0
    transition_timer = 0
    transitioning = False
    current_archetype = 'normal'

    # Upgrade state
    upgrade_choices = []
    selected_upgrade_idx = 0

    class_options = [
        ('1', 'vampire', '🧛 vs 🏹 Hunter', (200,30,30)), ('2', 'zombie', '🧟 vs 🪖 Soldier', (30,160,30)),
        ('3', 'witch', '🧙 vs 🔥 Inquisitor', (160,30,160)), ('4', 'werewolf', '🐺 vs 🪤 Trapper', (220,120,30)),
        ('5', 'ghost', '👻 vs 🧪 Ghostbuster', (150,220,255)), ('6', 'alien', '👽 vs 🕵️ Agent', (50,255,50)),
        ('7', 'shadow', '🥷 vs 🔦 Lightbringer', (60,0,90)), ('8', 'necromancer', '💀 vs 📿 Priest', (120,120,130)),
        ('9', 'slime', '🟢 vs 🧹 Janitor', (180,220,50)), ('0', 'siren', '🧜 vs 🧏 Guard', (255,100,150))
    ]
    difficulty_options = [
        ('1', 'easy', '🟢 EASY', (100,255,100)), ('2', 'normal', '🟡 NORMAL', (255,220,100)), ('3', 'hard', '🔴 HARD', (255,100,100))
    ]

    def start_run(diff=None):
        nonlocal player, villagers, enemies, enemy_bullets, enemy_traps, powerups
        nonlocal score, combo, combo_timer, best_combo, time_counter, powerup_spawn_timer, slowmo_active, run_stats, new_best, death_message
        nonlocal current_wave, wave_humans_total, wave_humans_converted, wave_start_time, wave_damage_taken, transition_timer, transitioning, current_archetype
        nonlocal adaptive_diff, upgrade_choices, selected_upgrade_idx
        d = diff or selected_difficulty
        player = Player(selected_class, emoji_mgr, d)
        villagers = []; enemies = []; enemy_bullets = []; enemy_traps = []; powerups = []
        score = 0; combo = 0; combo_timer = 0; best_combo = 0
        time_counter = 0; powerup_spawn_timer = 300; slowmo_active = 0
        new_best = False; death_message = ""
        current_wave = 1; wave_humans_total = 0; wave_humans_converted = 0
        wave_start_time = 0; wave_damage_taken = 0; transition_timer = 0; transitioning = False
        current_archetype = 'normal'
        adaptive_diff = AdaptiveDifficulty()
        upgrade_choices = []; selected_upgrade_idx = 0
        run_stats = {'conversions': 0, 'max_combo': 0, 'damage_taken': 0, 'won': False,
                     'time_seconds': 0, 'golden_converted': 0, 'criticals': 0, 'max_horde': 0,
                     'wave_no_damage': False, 'wave_fast': False, 'elites_killed': 0, 'bosses_killed': 0,
                     'upgrade_count': 0}
        spawn_wave(current_wave)
        cfg = get_wave_config(current_wave, adaptive_diff)
        wave_announcer.trigger(1, cfg)
        # Chrono start upgrade
        if player.chrono_start:
            player.buffs['slowmo'] = 180

    def spawn_wave(wave):
        nonlocal villagers, enemies, wave_humans_total, wave_humans_converted, wave_start_time, wave_damage_taken, current_archetype
        cfg = get_wave_config(wave, adaptive_diff)
        current_archetype = cfg['archetype']
        # Apply player's golden bonus
        golden_chance = min(0.9, cfg['golden_chance'] + player.golden_bonus)
        cfg['golden_chance'] = golden_chance

        villagers = [v for v in villagers if v.converted and v.alive]
        if daily_mode:
            rng = random.Random(get_daily_seed() + hash(selected_difficulty) + wave)
        else:
            rng = random

        golden_index = rng.randint(0, cfg['humans'] - 1) if rng.random() < cfg['golden_chance'] else -1
        for i in range(cfg['humans']):
            vx = rng.randint(50, WIDTH-50); vy = rng.randint(50, HEIGHT-50)
            attempts = 0
            while dist_sq(vx, vy, player.x, player.y) < 22500 and attempts < 20:
                vx = rng.randint(50, WIDTH-50); vy = rng.randint(50, HEIGHT-50); attempts += 1
            villagers.append(Villager(vx, vy, emoji_mgr, is_golden=(i == golden_index)))

        diff = DIFFICULTY[selected_difficulty]
        wave_hp_mult = cfg['hp_mult']; wave_speed_mult = cfg['speed_mult']; wave_backup_mult = cfg['backup_mult']
        elite_indices = set()
        if cfg['elite_count'] > 0 and cfg['enemies'] > 0:
            elite_indices = set(rng.sample(range(cfg['enemies']), min(cfg['elite_count'], cfg['enemies'])))

        for i in range(cfg['enemies']):
            ex = rng.choice([50, WIDTH-50]); ey = rng.choice([50, HEIGHT-50])
            if cfg['is_boss'] and i == 0:
                enemies.append(Enemy(ex, ey, selected_class, emoji_mgr, selected_difficulty,
                                    wave_hp_mult, wave_speed_mult, wave_backup_mult, 'none', is_boss=True))
            else:
                elite_type = 'none'
                if i in elite_indices:
                    elite_type = rng.choice(['shielded', 'fast', 'tank', 'bomber'])
                enemies.append(Enemy(ex, ey, selected_class, emoji_mgr, selected_difficulty,
                                    wave_hp_mult, wave_speed_mult, wave_backup_mult, elite_type, is_boss=False))

        if cfg['archetype'] == 'breather':
            for _ in range(3):
                px = rng.randint(60, WIDTH-60); py = rng.randint(60, HEIGHT-60)
                powerups.append(PowerUp(px, py, rng.choice(POWERUP_TYPES), emoji_mgr))

        wave_humans_total = cfg['humans']; wave_humans_converted = 0
        wave_start_time = time_counter; wave_damage_taken = 0

        # Phylactery reset per wave
        if player.phylactery:
            player.phylactery_used = False

    def complete_wave():
        nonlocal current_wave, transition_timer, transitioning, score, run_stats, data
        nonlocal wave_humans_converted, adaptive_diff, upgrade_choices, selected_upgrade_idx

        wave_time = (time_counter - wave_start_time) / 60
        wave_bonus = int(current_wave * 100 * player.score_mult)
        score += wave_bonus

        healed = False
        if player.hp < player.max_hp:
            player.hp += 1; healed = True

        run_stats['wave_no_damage'] = (wave_damage_taken == 0)
        run_stats['wave_fast'] = (wave_time < 20)
        run_stats['upgrade_count'] = len(player.upgrades)

        if wave_damage_taken == 0:
            data['perfect_wave_streak'] = data.get('perfect_wave_streak', 0) + 1
        else:
            data['perfect_wave_streak'] = 0
        if current_wave > data.get('best_wave', 0):
            data['best_wave'] = current_wave

        adaptive_diff.record_wave(wave_time, wave_damage_taken, wave_humans_total, current_wave)

        reward_parts = [f"+{wave_bonus} points"]
        if healed: reward_parts.append("+1 ❤️ healed")
        if wave_damage_taken == 0: reward_parts.append("FLAWLESS! 💯")
        heat_label, heat_color = adaptive_diff.get_heat_label()
        reward_parts.append(f"Heat: {heat_label}")
        reward_text = "  |  ".join(reward_parts)

        is_endless_unlock = (current_wave == 10)
        wave_complete_popup.trigger(current_wave, reward_text, is_endless_unlock, current_archetype)

        # Generate upgrade choices
        upgrade_choices = generate_upgrade_choices(selected_class, current_wave)
        selected_upgrade_idx = 0

        earned = check_achievements(data, run_stats)
        for a in earned: achievement_popup.trigger(a)
        save_data(data)

        current_wave += 1
        transition_timer = 120  # Show complete popup briefly
        transitioning = True

    def apply_selected_upgrade():
        nonlocal upgrade_choices, selected_upgrade_idx, state
        if not upgrade_choices: return
        upgrade = upgrade_choices[selected_upgrade_idx]

        # Check max stacks
        current_count = player.count_upgrade(upgrade['id'])
        if current_count >= upgrade['max_stacks']:
            # Find another upgrade that's not maxed
            for i, u in enumerate(upgrade_choices):
                if player.count_upgrade(u['id']) < u['max_stacks']:
                    selected_upgrade_idx = i
                    upgrade = upgrade_choices[i]
                    break

        player.apply_upgrade(upgrade)
        run_stats['upgrade_count'] = len(player.upgrades)

        # Track legendaries
        if upgrade['rarity'] == 'legendary':
            data['total_legendaries'] = data.get('total_legendaries', 0) + 1

        # Check achievements
        earned = check_achievements(data, run_stats)
        for a in earned: achievement_popup.trigger(a)
        save_data(data)

        upgrade_choices = []
        # Now spawn next wave
        spawn_wave(current_wave)
        cfg = get_wave_config(current_wave, adaptive_diff)
        wave_announcer.trigger(current_wave, cfg)
        if player.chrono_start:
            player.buffs['slowmo'] = 180
        state = STATE_PLAYING

    def draw_upgrade_card(screen, upgrade, x, y, w, h, selected, idx):
        """Draw a single upgrade card."""
        rarity_color = RARITY_COLORS[upgrade['rarity']]

        # Check if maxed
        current_count = player.count_upgrade(upgrade['id'])
        maxed = current_count >= upgrade['max_stacks']

        # Card background
        card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_alpha = 220 if selected else 180
        card_surf.fill((20, 20, 30, bg_alpha))
        screen.blit(card_surf, (x, y))

        # Border (thicker if selected)
        border_color = rarity_color if not maxed else GRAY
        border_width = 4 if selected else 2
        pygame.draw.rect(screen, border_color, (x, y, w, h), border_width)

        # Selection glow
        if selected and not maxed:
            glow_surf = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
            pulse = int(50 + math.sin(time_counter * 0.15) * 30)
            pygame.draw.rect(glow_surf, (*rarity_color, pulse), (0, 0, w + 10, h + 10), 3)
            screen.blit(glow_surf, (x - 5, y - 5))

        # Key indicator
        key_text = f"[{idx + 1}]"
        draw_text(screen, key_text, 18, x + 10, y + 10, rarity_color if not maxed else GRAY)

        # Icon (using text emoji since we don't have all icons loaded)
        draw_text(screen, upgrade['icon'], 40, x + w // 2, y + 50, WHITE if not maxed else GRAY, center=True)

        # Name
        name_color = WHITE if not maxed else GRAY
        draw_text(screen, upgrade['name'], 18, x + w // 2, y + 95, name_color, center=True)

        # Description (wrap if needed)
        desc_color = (200, 200, 200) if not maxed else GRAY
        # Split desc into lines if too long
        desc = upgrade['desc']
        if len(desc) > 25:
            words = desc.split()
            line1 = ""; line2 = ""
            for word in words:
                if len(line1 + " " + word) < 25:
                    line1 = (line1 + " " + word).strip()
                else:
                    line2 = (line2 + " " + word).strip()
            draw_text(screen, line1, 13, x + w // 2, y + 125, desc_color, center=True)
            if line2:
                draw_text(screen, line2, 13, x + w // 2, y + 142, desc_color, center=True)
        else:
            draw_text(screen, desc, 13, x + w // 2, y + 130, desc_color, center=True)

        # Rarity label
        rarity_label = upgrade['rarity'].upper()
        draw_text(screen, rarity_label, 14, x + w // 2, y + h - 30, rarity_color if not maxed else GRAY, center=True)

        # Stack indicator
        if upgrade['max_stacks'] > 1:
            stack_text = f"{current_count}/{upgrade['max_stacks']}"
            draw_text(screen, stack_text, 12, x + w - 15, y + 15, rarity_color if not maxed else GRAY)

        if maxed:
            draw_text(screen, "MAXED", 16, x + w // 2, y + h // 2, GRAY, center=True)

    while True:
        if hit_stop.update():
            pygame.display.flip()
            clock.tick(FPS)
            continue

        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == STATE_PLAYING: state = STATE_PAUSED
                    elif state == STATE_PAUSED: state = STATE_PLAYING
                    elif state == STATE_ACHIEVEMENTS: state = STATE_MENU
                    elif state in (STATE_WIN, STATE_LOSE): state = STATE_MENU

                if state == STATE_TUTORIAL:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = STATE_MENU

                elif state == STATE_MENU:
                    for k, cls, _, _ in class_options:
                        if event.key == getattr(pygame, f'K_{k}'):
                            selected_class = cls
                    if event.key == pygame.K_RETURN: state = STATE_DIFFICULTY
                    if event.key == pygame.K_a: state = STATE_ACHIEVEMENTS
                    if event.key == pygame.K_d:
                        daily_mode = True; selected_difficulty = 'normal'
                        start_run('normal'); state = STATE_PLAYING

                elif state == STATE_DIFFICULTY:
                    if event.key == pygame.K_1: selected_difficulty = 'easy'
                    if event.key == pygame.K_2: selected_difficulty = 'normal'
                    if event.key == pygame.K_3: selected_difficulty = 'hard'
                    if event.key == pygame.K_RETURN:
                        daily_mode = False; start_run(); state = STATE_PLAYING

                elif state == STATE_UPGRADE:
                    if event.key == pygame.K_1 and len(upgrade_choices) >= 1:
                        selected_upgrade_idx = 0
                    elif event.key == pygame.K_2 and len(upgrade_choices) >= 2:
                        selected_upgrade_idx = 1
                    elif event.key == pygame.K_3 and len(upgrade_choices) >= 3:
                        selected_upgrade_idx = 2
                    elif event.key == pygame.K_LEFT:
                        selected_upgrade_idx = max(0, selected_upgrade_idx - 1)
                    elif event.key == pygame.K_RIGHT:
                        selected_upgrade_idx = min(len(upgrade_choices) - 1, selected_upgrade_idx + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Apply the selected upgrade
                        apply_selected_upgrade()

                elif state in (STATE_WIN, STATE_LOSE):
                    if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                        start_run(); state = STATE_PLAYING
                    if event.key == pygame.K_c and HAS_CLIPBOARD:
                        text = f"🎃 Monster Infection 🎃\nClass: {selected_class.title()}\nWave: {current_wave-1 if state == STATE_WIN else current_wave}\nScore: {score}\nBest Combo: {best_combo}x\nUpgrades: {len(player.upgrades) if player else 0}\nCan you beat me?"
                        try: pyperclip.copy(text)
                        except: pass

        # =====================================================================
        # TUTORIAL
        # =====================================================================
        if state == STATE_TUTORIAL:
            screen.blit(bg_surface, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            draw_text(screen, "🎃 WELCOME TO MONSTER INFECTION 🎃", 34, WIDTH//2, 60, GOLD, center=True)
            draw_text(screen, "You are a monster. Convert all the humans.", 20, WIDTH//2, 110, WHITE, center=True)
            draw_text(screen, "Survive waves of Hunters and UPGRADE your powers!", 20, WIDTH//2, 135, (150, 200, 255), center=True)
            draw_text(screen, "CONTROLS", 24, WIDTH//2, 175, GOLD, center=True)
            draw_text(screen, "WASD / Arrows — Move   |   SPACE — Special Ability   |   ESC — Pause", 16, WIDTH//2, 205, WHITE, center=True)
            draw_text(screen, "UPGRADE SYSTEM", 24, WIDTH//2, 240, GOLD, center=True)
            draw_text(screen, "After each wave, pick 1 of 3 upgrades:", 16, WIDTH//2, 270, WHITE, center=True)
            draw_text(screen, "⬜ Common   🟦 Rare   🟪 Epic   🟨 Legendary", 16, WIDTH//2, 295, WHITE, center=True)
            draw_text(screen, "Each class has unique upgrades that enhance their playstyle!", 16, WIDTH//2, 320, (255, 200, 100), center=True)
            draw_text(screen, "WAVE TYPES", 24, WIDTH//2, 355, GOLD, center=True)
            draw_text(screen, "🌊 Normal   👥 Horde   ⚔️ Elite   ☕ Breather   💀 Boss (every 10)", 16, WIDTH//2, 385, WHITE, center=True)
            draw_text(screen, "ELITE ENEMIES", 24, WIDTH//2, 420, GOLD, center=True)
            draw_text(screen, "🛡️ Shielded (half damage)   ⚡ Fast (1.8x speed)   💪 Tank (huge HP)   💣 Bomber (explodes)", 14, WIDTH//2, 450, WHITE, center=True)
            draw_text(screen, "ADAPTIVE DIFFICULTY - The game watches how you play and adjusts!", 15, WIDTH//2, 485, (150, 255, 150), center=True)
            pulse = int(200 + math.sin(time_counter * 0.1) * 55)
            draw_text(screen, "Press ENTER or SPACE to start", 22, WIDTH//2, 555, (pulse, pulse, pulse), center=True)
            time_counter += 1

        # =====================================================================
        # MENU
        # =====================================================================
        elif state == STATE_MENU:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            draw_text(screen, "🎃 MONSTER INFECTION 🎃", 44, WIDTH//2, 50, GOLD, center=True)
            best_wave = data.get('best_wave', 0); best = data['best_score']
            if best_wave > 0 or best > 0:
                info = []
                if best_wave > 0: info.append(f"🌊 Best Wave: {best_wave}" + (" (Endless!)" if best_wave > 10 else "/10"))
                if best > 0: info.append(f"🏆 Best Score: {best}")
                draw_text(screen, "  |  ".join(info), 18, WIDTH//2, 95, GOLD, center=True)
            start_y = 125 if (best_wave > 0 or best > 0) else 140; spacing = 34
            for i, (key, cls, desc, color) in enumerate(class_options):
                yp = start_y + i * spacing
                draw_text(screen, f"{key}. {desc}", 20, WIDTH//2, yp, color, center=True)
                if selected_class == cls:
                    pygame.draw.rect(screen, WHITE, (WIDTH//2-220, yp-10, 440, 30), 2)
            draw_text(screen, "[ENTER] Play   [A] Achievements   [D] Daily Challenge", 16, WIDTH//2, 530, GRAY, center=True)
            draw_text(screen, f"Total Wins: {data['total_wins']}   |   Achievements: {len(data['achievements'])}/{len(ACHIEVEMENTS)}", 16, WIDTH//2, 555, GRAY, center=True)
            time_counter += 1

        # =====================================================================
        # ACHIEVEMENTS
        # =====================================================================
        elif state == STATE_ACHIEVEMENTS:
            screen.blit(bg_surface, (0, 0))
            draw_text(screen, "🏆 ACHIEVEMENTS 🏆", 40, WIDTH//2, 40, GOLD, center=True)
            y = 85
            for ach in ACHIEVEMENTS:
                earned = ach['id'] in data['achievements']
                color = GOLD if earned else GRAY
                status = "✓" if earned else "✗"
                draw_text(screen, f"{status} {ach['icon']} {ach['name']}", 20, 100, y, color)
                draw_text(screen, ach['desc'], 15, 400, y + 3, color if earned else GRAY)
                y += 36
            draw_text(screen, "Press [ESC] to go back", 18, WIDTH//2, 560, GRAY, center=True)

        # =====================================================================
        # DIFFICULTY
        # =====================================================================
        elif state == STATE_DIFFICULTY:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            draw_text(screen, "SELECT DIFFICULTY", 44, WIDTH//2, 150, WHITE, center=True)
            for i, (key, diff, label, color) in enumerate(difficulty_options):
                yp = 250 + i * 70
                draw_text(screen, f"{key}. {label}", 36, WIDTH//2, yp, color, center=True)
                if selected_difficulty == diff:
                    pygame.draw.rect(screen, WHITE, (WIDTH//2-180, yp-20, 360, 50), 3)
                mult = DIFFICULTY[diff]['score_mult']
                draw_text(screen, f"Score x{mult}", 18, WIDTH//2, yp + 25, GRAY, center=True)
            draw_text(screen, "Use [1-3] to select, [ENTER] to start", 20, WIDTH//2, 520, GRAY, center=True)
            draw_text(screen, "Press [ESC] to go back", 18, WIDTH//2, 550, GRAY, center=True)
            time_counter += 1

        # =====================================================================
        # PAUSED
        # =====================================================================
        elif state == STATE_PAUSED:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            for v in villagers: v.draw(screen)
            for e in enemies: e.draw(screen)
            if player: player.draw(screen)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150)); screen.blit(overlay, (0, 0))
            draw_text(screen, "⏸ PAUSED", 64, WIDTH//2, HEIGHT//2-30, WHITE, center=True)
            draw_text(screen, "Press [ESC] to resume", 24, WIDTH//2, HEIGHT//2+30, GRAY, center=True)
            draw_text(screen, f"Wave {current_wave}  |  Score: {score}  |  Combo: {combo}x", 22, WIDTH//2, HEIGHT//2+80, GOLD, center=True)
            time_counter += 1

        # =====================================================================
        # UPGRADE SELECTION
        # =====================================================================
        elif state == STATE_UPGRADE:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))

            # Draw game state dimmed in background
            dim_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim_overlay.fill((0, 0, 0, 100))
            screen.blit(dim_overlay, (0, 0))

            for v in villagers: v.draw(screen)
            if player: player.draw(screen)

            # Darker overlay for focus
            focus_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            focus_overlay.fill((0, 0, 0, 130))
            screen.blit(focus_overlay, (0, 0))

            # Header
            draw_text(screen, "⬆️ CHOOSE YOUR UPGRADE ⬆️", 40, WIDTH//2, 50, GOLD, center=True)
            draw_text(screen, f"Wave {current_wave - 1} Complete!", 20, WIDTH//2, 95, WHITE, center=True)

            # Draw 3 upgrade cards
            if upgrade_choices:
                card_w = 200; card_h = 220
                total_w = card_w * 3 + 40
                start_x = WIDTH // 2 - total_w // 2
                card_y = 140

                for i, upgrade in enumerate(upgrade_choices):
                    cx = start_x + i * (card_w + 20)
                    draw_upgrade_card(screen, upgrade, cx, card_y, card_w, card_h, i == selected_upgrade_idx, i)

            # Instructions
            draw_text(screen, "Use [1] [2] [3] or [←][→] + [ENTER] to select", 18, WIDTH//2, 400, WHITE, center=True)

            # Show owned upgrades (compact)
            if player and player.upgrades:
                draw_text(screen, f"Owned Upgrades ({len(player.upgrades)}):", 16, WIDTH//2, 440, GRAY, center=True)
                # Show as small icons in a row
                upgrade_icons = []
                for uid in player.upgrades:
                    for u in UPGRADES:
                        if u['id'] == uid:
                            upgrade_icons.append(u['icon'])
                            break
                # Display in rows of 10
                icons_text = " ".join(upgrade_icons[:20])
                if len(upgrade_icons) > 20:
                    icons_text += f" +{len(upgrade_icons) - 20}"
                draw_text(screen, icons_text, 18, WIDTH//2, 465, WHITE, center=True)

            # Achievement popups still show
            achievement_popup.update()
            achievement_popup.draw(screen)

            time_counter += 1

        # =====================================================================
        # WAVE TRANSITION
        # =====================================================================
        elif state == STATE_WAVE_TRANSITION:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            for v in villagers: v.draw(screen)
            if player: player.draw(screen)
            wave_complete_popup.update()
            wave_complete_popup.draw(screen)
            achievement_popup.update()
            achievement_popup.draw(screen)
            transition_timer -= 1
            time_counter += 1
            if transition_timer <= 0:
                # Move to upgrade selection
                state = STATE_UPGRADE

        # =====================================================================
        # PLAYING
        # =====================================================================
        elif state == STATE_PLAYING:
            time_counter += 1
            run_stats['time_seconds'] = time_counter // 60
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))

            keys = pygame.key.get_pressed()

            if player.buffs['slowmo'] > 0:
                slowmo_active = 1
                if time_counter % 2 != 0: player.update(keys)
            else:
                slowmo_active = 0; player.update(keys)

            if combo_timer > 0: combo_timer -= 1
            else: combo = 0

            powerup_spawn_timer -= 1
            spawn_threshold = int(500 / adaptive_diff.get_powerup_bonus())
            if powerup_spawn_timer <= 0 and len(powerups) < 3:
                px = random.randint(60, WIDTH-60); py = random.randint(60, HEIGHT-60)
                powerups.append(PowerUp(px, py, random.choice(POWERUP_TYPES), emoji_mgr))
                powerup_spawn_timer = random.randint(spawn_threshold - 100, spawn_threshold + 100)

            mult = 2 if player.buffs['multiplier'] > 0 else 1

            # --- Class-specific logic ---
            if player.char_class == 'werewolf':
                cc = sum(1 for v in villagers if v.converted and v.alive)
                player.speed = min(player.base_speed + cc * 0.15 * player.frenzy_mult, 7.5)
                # Howl dash
                if player.howl_dash and keys[pygame.K_SPACE] and player.howl_cd == 0:
                    player.x += player.last_dir[0] * 100; player.y += player.last_dir[1] * 100
                    player.x = max(player.radius, min(WIDTH - player.radius, player.x))
                    player.y = max(player.radius, min(HEIGHT - player.radius, player.y))
                    player.howl_cd = 600
                    particle_pool.spawn(player.x, player.y, player.color, 15, 'smoke')
            elif player.char_class == 'alien':
                beam_cd = int(40 * player.beam_cd_mult)
                if keys[pygame.K_SPACE] and player.ray_cooldown == 0:
                    # Orbital strike if upgrade
                    if player.orbital_strike and player.ray_cooldown == 0 and keys[pygame.K_LSHIFT]:
                        # Big AOE around player
                        particle_pool.spawn(player.x, player.y, (50, 255, 50), 50)
                        for v in villagers:
                            if not v.converted and v.alive and dist_sq(v.x, v.y, player.x, player.y) < 150*150:
                                base_points = 50 if v.is_golden else 10
                                points = base_points * max(1, combo) * mult
                                v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                                score += int(points); combo += 1; combo_timer = 120
                                wave_humans_converted += 1
                                run_stats['conversions'] += 1
                        player.ray_cooldown = 180
                    else:
                        closest = None; cd = float('inf')
                        for v in villagers:
                            if not v.converted and v.alive:
                                d = dist_sq(v.x, v.y, player.x, player.y)
                                if d < cd: cd = d; closest = v
                        if closest:
                            dx = closest.x - player.x; dy = closest.y - player.y
                            d = math.sqrt(dx*dx + dy*dy)
                            if d > 0:
                                player.rays.append([player.x, player.y, (dx/d)*9, (dy/d)*9, 100])
                                player.ray_cooldown = beam_cd
                new_rays = []
                for r in player.rays:
                    r[0] += r[2]; r[1] += r[3]; r[4] -= 1
                    hit = False
                    for v in villagers:
                        hit_radius = (12 + v.radius + player.beam_aoe) if player.beam_aoe > 0 else (12 + v.radius)
                        if not v.converted and v.alive and point_in_radius_sq(r[0], r[1], v.x, v.y, hit_radius):
                            base_points = 50 if v.is_golden else 10
                            is_critical = random.random() < (0.1 + player.crit_bonus)
                            points = base_points * (2 if is_critical else 1) * max(1, combo) * mult * player.score_mult
                            v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                            particle_pool.spawn(v.x, v.y, GOLD if v.is_golden else player.color, 12 if v.is_golden else 8)
                            floating_numbers.spawn(v.x, v.y, f"+{int(points)}", GOLD if v.is_golden else player.color, 28 if v.is_golden else 22)
                            if is_critical:
                                floating_numbers.spawn(v.x, v.y - 25, "CRITICAL!", (255, 100, 255), 20)
                                particle_pool.spawn(v.x, v.y, (255, 100, 255), 15)
                                run_stats['criticals'] = run_stats.get('criticals', 0) + 1
                            if v.is_golden:
                                run_stats['golden_converted'] = run_stats.get('golden_converted', 0) + 1
                                combo_flash.trigger("✨ GOLDEN! ✨", GOLD); hit_stop.trigger(10)
                            score += int(points)
                            combo += 1; combo_timer = int(120 * player.combo_timer_mult)
                            if combo > best_combo: best_combo = combo
                            run_stats['conversions'] += 1
                            run_stats['max_combo'] = max(run_stats['max_combo'], combo)
                            wave_humans_converted += 1

                            # Vampiric / blood frenzy heals
                            if player.vampiric:
                                player.conversions_since_heal += 1
                                if player.conversions_since_heal >= 5 and player.hp < player.max_hp:
                                    player.hp += 1; player.conversions_since_heal = 0
                                    floating_numbers.spawn(player.x, player.y, "+1 ❤", (100, 255, 100), 20)
                            if player.blood_frenzy and player.hp < player.max_hp:
                                player.hp += 1
                                floating_numbers.spawn(player.x, player.y, "+1 ❤", (100, 255, 100), 20)

                            if combo in COMBO_MILESTONES:
                                m = COMBO_MILESTONES[combo]
                                combo_flash.trigger(m['text'], m['color'])
                                hit_stop.trigger(8)
                                particle_pool.spawn(player.x, player.y, m['color'], 30)
                            # AOE beam converts nearby too
                            if player.beam_aoe > 0:
                                for v2 in villagers:
                                    if v2 is not v and not v2.converted and v2.alive:
                                        if dist_sq(v2.x, v2.y, r[0], r[1]) < player.beam_aoe * player.beam_aoe:
                                            v2.converted = True; v2.converted_to = player.emoji_name; v2.converted_color = player.color
                                            score += int(10 * max(1, combo) * mult * player.score_mult)
                                            combo += 1; wave_humans_converted += 1
                                            run_stats['conversions'] += 1
                            hit = True; break
                    if not hit and r[4] > 0 and 0 < r[0] < WIDTH and 0 < r[1] < HEIGHT:
                        new_rays.append(r)
                player.rays = new_rays
            elif player.char_class == 'ghost':
                for t in player.trail:
                    trail_r = (18 + v.radius if False else 18) * player.trail_width_mult
                    for v in villagers:
                        if not v.converted and v.alive and point_in_radius_sq(t[0], t[1], v.x, v.y, trail_r + v.radius):
                            base_points = 50 if v.is_golden else 10
                            is_critical = random.random() < (0.1 + player.crit_bonus)
                            points = base_points * (2 if is_critical else 1) * max(1, combo) * mult * player.score_mult
                            v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                            particle_pool.spawn(v.x, v.y, GOLD if v.is_golden else player.color, 12 if v.is_golden else 8)
                            floating_numbers.spawn(v.x, v.y, f"+{int(points)}", GOLD if v.is_golden else player.color, 28 if v.is_golden else 22)
                            if is_critical:
                                floating_numbers.spawn(v.x, v.y - 25, "CRITICAL!", (255, 100, 255), 20)
                                run_stats['criticals'] = run_stats.get('criticals', 0) + 1
                            if v.is_golden:
                                run_stats['golden_converted'] = run_stats.get('golden_converted', 0) + 1
                                combo_flash.trigger("✨ GOLDEN! ✨", GOLD); hit_stop.trigger(10)
                            score += int(points)
                            combo += 1; combo_timer = int(120 * player.combo_timer_mult)
                            if combo > best_combo: best_combo = combo
                            run_stats['conversions'] += 1
                            run_stats['max_combo'] = max(run_stats['max_combo'], combo)
                            wave_humans_converted += 1
                            if player.vampiric:
                                player.conversions_since_heal += 1
                                if player.conversions_since_heal >= 5 and player.hp < player.max_hp:
                                    player.hp += 1; player.conversions_since_heal = 0
                            if player.blood_frenzy and player.hp < player.max_hp: player.hp += 1
                            if combo in COMBO_MILESTONES:
                                m = COMBO_MILESTONES[combo]
                                combo_flash.trigger(m['text'], m['color']); hit_stop.trigger(8)
                    # Trail damages enemies
                    if player.trail_damage > 0:
                        for e in enemies:
                            if point_in_radius_sq(t[0], t[1], e.x, e.y, trail_r + e.radius):
                                if e.take_damage(player.trail_damage):
                                    particle_pool.spawn(e.x, e.y, (255, 200, 100), 15)
            elif player.char_class == 'shadow':
                dash_dist = player.dash_distance
                if keys[pygame.K_SPACE] and player.teleport_cd == 0:
                    particle_pool.spawn(player.x, player.y, player.color, 10, 'smoke')
                    # Shadow clone upgrade
                    if player.shadow_clone:
                        clone_x, clone_y = player.x, player.y
                        # Clone stays briefly - handled as a temporary grave-like thing
                        player.graves.append([clone_x, clone_y])  # Reuse graves for clone
                    player.x += player.last_dir[0] * dash_dist
                    player.y += player.last_dir[1] * dash_dist
                    player.x = max(player.radius, min(WIDTH - player.radius, player.x))
                    player.y = max(player.radius, min(HEIGHT - player.radius, player.y))
                    particle_pool.spawn(player.x, player.y, player.color, 10, 'smoke')
                    player.teleport_cd = int(60 * player.dash_cd_mult)
            elif player.char_class == 'necromancer':
                if keys[pygame.K_SPACE] and player.grave_cd == 0:
                    player.graves.append([player.x, player.y])
                    particle_pool.spawn(player.x, player.y, (120,120,130), 10, 'smoke')
                    if len(player.graves) > player.max_graves: player.graves.pop(0)
                    player.grave_cd = 90
            elif player.char_class == 'siren':
                if keys[pygame.K_SPACE] and player.charm_cd == 0:
                    player.charm_active = int(180 * player.charm_duration_mult)
                    player.charm_cd = 360
                    particle_pool.spawn(player.x, player.y, player.color, 12)

            spatial_grid.clear()
            for v in villagers:
                if v.alive: spatial_grid.insert(v)

            converted_minions = [v for v in villagers if v.converted and v.alive]
            unconverted = [v for v in villagers if not v.converted and v.alive]
            run_stats['max_horde'] = max(run_stats['max_horde'], len(converted_minions))

            for e in enemies:
                if slowmo_active and time_counter % 2 != 0: continue
                e.update(player, converted_minions, enemy_bullets, enemy_traps, enemies, particle_pool, floating_numbers)
                if player.iframes == 0 and check_collision_sq(player, e):
                    if player.shield:
                        player.shield = False
                        particle_pool.spawn(player.x, player.y, (100,200,255), 12)
                        floating_numbers.spawn(player.x, player.y, "BLOCKED!", (100, 200, 255), 24)
                    else:
                        player.hp -= 1
                        wave_damage_taken += 1
                        run_stats['damage_taken'] += 1
                        particle_pool.spawn(player.x, player.y, (255,50,50), 10, 'blood')
                        floating_numbers.spawn(player.x, player.y, "-1 ❤", (255, 80, 80), 28)
                        hit_stop.trigger(4)
                        # Split on hit (slime)
                        if player.split_on_hit:
                            player.puddles.append([player.x, player.y, 600, 50])
                            particle_pool.spawn(player.x, player.y, player.color, 30)
                    iframe_duration = int(60 * player.iframe_mult) + player.iframe_bonus
                    player.iframes = iframe_duration
                    dx = player.x - e.x; dy = player.y - e.y
                    d = math.sqrt(dx*dx + dy*dy)
                    if d > 0:
                        player.x = max(player.radius, min(WIDTH-player.radius, player.x + (dx/d)*50))
                        player.y = max(player.radius, min(HEIGHT-player.radius, player.y + (dy/d)*50))
                    killed = e.take_damage(player.bump_damage + (1 if player.buffs['damage'] > 0 else 0))
                    particle_pool.spawn(e.x, e.y, (255,200,100), 8)
                    if killed:
                        if e.elite_type == 'bomber':
                            particle_pool.spawn(e.x, e.y, (255, 100, 50), 30)
                            if dist_sq(player.x, player.y, e.x, e.y) < 100*100 and player.iframes == 0:
                                if not player.shield:
                                    player.hp -= 1; wave_damage_taken += 1; run_stats['damage_taken'] += 1
                                    player.iframes = int(60 * player.iframe_mult) + player.iframe_bonus
                                    floating_numbers.spawn(player.x, player.y, "BOOM! -1 ❤", (255, 100, 50), 28)
                        if e.elite_type != 'none':
                            run_stats['elites_killed'] = run_stats.get('elites_killed', 0) + 1
                            data['total_elites_killed'] = data.get('total_elites_killed', 0) + 1
                        if e.is_boss:
                            run_stats['bosses_killed'] = run_stats.get('bosses_killed', 0) + 1
                            data['total_bosses_killed'] = data.get('total_bosses_killed', 0) + 1
                            combo_flash.trigger("⚔️ BOSS DEFEATED! ⚔️", GOLD)
                            hit_stop.trigger(15)
                            particle_pool.spawn(e.x, e.y, GOLD, 50)
                            score += 500
                            floating_numbers.spawn(e.x, e.y, "+500 BOSS!", GOLD, 32)
                for v in converted_minions:
                    if check_collision_sq(v, e):
                        v.alive = False
                        particle_pool.spawn(v.x, v.y, (255,50,50), 8, 'blood')
            enemies = [e for e in enemies if e.hp > 0]

            charm_active = player.charm_active if player.char_class == 'siren' else 0
            unconverted_count = 0
            aura_sq = (player.aura + 14) ** 2 if player.aura > 0 else 0

            for v in villagers:
                if not v.alive: continue
                if slowmo_active and time_counter % 2 != 0 and not v.converted: continue
                v.update(unconverted, enemies, player, player.emoji_name, charm_active, player.minion_speed_mult)
                if not v.converted:
                    unconverted_count += 1
                    converted_now = False
                    if check_collision_sq(player, v): converted_now = True
                    elif aura_sq > 0 and dist_sq(player.x, player.y, v.x, v.y) < aura_sq: converted_now = True
                    if not converted_now:
                        nearby = spatial_grid.get_nearby(v.x, v.y, v.radius + 14)
                        for mv in nearby:
                            if mv.converted and mv.alive and check_collision_sq(mv, v):
                                converted_now = True; break
                    # Hypnotic: charmed humans convert nearby
                    if not converted_now and player.hypnotic and charm_active > 0:
                        for mv in nearby:
                            if mv.converted and mv.alive and dist_sq(mv.x, mv.y, v.x, v.y) < 50*50:
                                converted_now = True; break
                    # Minion aura (witch)
                    if not converted_now and player.minion_aura > 0:
                        for mv in converted_minions:
                            if dist_sq(mv.x, mv.y, v.x, v.y) < (player.minion_aura + v.radius) ** 2:
                                converted_now = True; break
                    if converted_now:
                        base_points = 50 if v.is_golden else 10
                        is_critical = random.random() < (0.1 + player.crit_bonus)
                        points = base_points * (2 if is_critical else 1) * max(1, combo) * mult * player.score_mult
                        v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                        particle_pool.spawn(v.x, v.y, GOLD if v.is_golden else player.color, 12 if v.is_golden else 8)
                        floating_numbers.spawn(v.x, v.y, f"+{int(points)}", GOLD if v.is_golden else player.color, 28 if v.is_golden else 22)
                        if is_critical:
                            floating_numbers.spawn(v.x, v.y - 25, "CRITICAL!", (255, 100, 255), 20)
                            particle_pool.spawn(v.x, v.y, (255, 100, 255), 15)
                            run_stats['criticals'] = run_stats.get('criticals', 0) + 1
                        if v.is_golden:
                            run_stats['golden_converted'] = run_stats.get('golden_converted', 0) + 1
                            combo_flash.trigger("✨ GOLDEN! ✨", GOLD); hit_stop.trigger(10)
                        score += int(points)
                        combo += 1; combo_timer = int(120 * player.combo_timer_mult)
                        if combo > best_combo: best_combo = combo
                        run_stats['conversions'] += 1
                        run_stats['max_combo'] = max(run_stats['max_combo'], combo)
                        wave_humans_converted += 1
                        # Healing upgrades
                        if player.vampiric:
                            player.conversions_since_heal += 1
                            if player.conversions_since_heal >= 5 and player.hp < player.max_hp:
                                player.hp += 1; player.conversions_since_heal = 0
                                floating_numbers.spawn(player.x, player.y, "+1 ❤", (100, 255, 100), 20)
                        if player.blood_frenzy and player.hp < player.max_hp:
                            player.hp += 1
                            floating_numbers.spawn(player.x, player.y, "+1 ❤", (100, 255, 100), 20)
                        if combo in COMBO_MILESTONES:
                            m = COMBO_MILESTONES[combo]
                            combo_flash.trigger(m['text'], m['color'])
                            hit_stop.trigger(8)
                            particle_pool.spawn(player.x, player.y, m['color'], 30)

            # Necromancer graves
            if player.char_class == 'necromancer':
                grave_range_sq = (player.grave_range + 14) ** 2
                for g in player.graves:
                    for v in unconverted:
                        if v.alive and not v.converted and dist_sq(g[0], g[1], v.x, v.y) < grave_range_sq:
                            base_points = 50 if v.is_golden else 10
                            points = base_points * max(1, combo) * mult * player.score_mult
                            v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                            particle_pool.spawn(v.x, v.y, player.color, 8)
                            floating_numbers.spawn(v.x, v.y, f"+{int(points)}", player.color, 22)
                            score += int(points)
                            combo += 1; combo_timer = int(120 * player.combo_timer_mult)
                            run_stats['conversions'] += 1
                            run_stats['max_combo'] = max(run_stats['max_combo'], combo)
                            wave_humans_converted += 1
                            if player.vampiric:
                                player.conversions_since_heal += 1
                                if player.conversions_since_heal >= 5 and player.hp < player.max_hp:
                                    player.hp += 1; player.conversions_since_heal = 0
                            if player.blood_frenzy and player.hp < player.max_hp: player.hp += 1

            # Slime puddles
            if player.char_class == 'slime':
                for p in player.puddles:
                    pr_sq = (p[3] + 14) ** 2
                    for v in unconverted:
                        if v.alive and not v.converted and dist_sq(p[0], p[1], v.x, v.y) < pr_sq:
                            base_points = 50 if v.is_golden else 10
                            points = base_points * max(1, combo) * mult * player.score_mult
                            v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                            particle_pool.spawn(v.x, v.y, player.color, 8)
                            floating_numbers.spawn(v.x, v.y, f"+{int(points)}", player.color, 22)
                            score += int(points)
                            combo += 1; combo_timer = int(120 * player.combo_timer_mult)
                            run_stats['conversions'] += 1
                            run_stats['max_combo'] = max(run_stats['max_combo'], combo)
                            wave_humans_converted += 1
                            if player.vampiric:
                                player.conversions_since_heal += 1
                                if player.conversions_since_heal >= 5 and player.hp < player.max_hp:
                                    player.hp += 1; player.conversions_since_heal = 0
                            if player.blood_frenzy and player.hp < player.max_hp: player.hp += 1
                    # Puddle damages enemies
                    if player.puddle_damage > 0:
                        for e in enemies:
                            if dist_sq(p[0], p[1], e.x, e.y) < pr_sq:
                                if time_counter % 30 == 0:  # Damage per 0.5s
                                    if e.take_damage(player.puddle_damage):
                                        particle_pool.spawn(e.x, e.y, (255, 200, 100), 10)

            # Spell echo (witch)
            if player.spell_echo and player.spell_echo_timer == 0 and player.aura > 0:
                # Convert all in aura
                for v in unconverted:
                    if v.alive and not v.converted and dist_sq(player.x, player.y, v.x, v.y) < player.aura * player.aura:
                        v.converted = True; v.converted_to = player.emoji_name; v.converted_color = player.color
                        particle_pool.spawn(v.x, v.y, player.color, 8)
                        score += int(10 * max(1, combo) * mult * player.score_mult)
                        combo += 1; wave_humans_converted += 1
                        run_stats['conversions'] += 1

            pr = player.radius
            new_bullets = []
            for b in enemy_bullets:
                if slowmo_active: b[0] += b[2]*0.5; b[1] += b[3]*0.5
                else: b[0] += b[2]; b[1] += b[3]
                b[5] -= 1
                alive = True
                if player.iframes == 0 and point_in_radius_sq(b[0], b[1], player.x, player.y, 10 + pr):
                    if player.shield:
                        player.shield = False
                        particle_pool.spawn(player.x, player.y, (100,200,255), 12)
                        floating_numbers.spawn(player.x, player.y, "BLOCKED!", (100, 200, 255), 24)
                    else:
                        player.hp -= 1; wave_damage_taken += 1; run_stats['damage_taken'] += 1
                        particle_pool.spawn(player.x, player.y, (255,50,50), 10, 'blood')
                        floating_numbers.spawn(player.x, player.y, "-1 ❤", (255, 80, 80), 28)
                        hit_stop.trigger(4)
                        if player.split_on_hit:
                            player.puddles.append([player.x, player.y, 600, 50])
                    player.iframes = int(60 * player.iframe_mult) + player.iframe_bonus; alive = False
                if alive:
                    for v in converted_minions:
                        if point_in_radius_sq(b[0], b[1], v.x, v.y, 10 + v.radius):
                            if b[4] == 'necromancer': v.converted = False; v.color = HUMAN_COLOR
                            else: v.alive = False; particle_pool.spawn(v.x, v.y, (255,50,50), 8, 'blood')
                            alive = False; break
                if alive and b[4] == 'slime' and player.char_class == 'slime':
                    player.puddles = [p for p in player.puddles if dist_sq(b[0], b[1], p[0], p[1]) > p[3] * p[3]]
                if alive and b[4] == 'necromancer' and player.char_class == 'necromancer':
                    player.graves = [g for g in player.graves if dist_sq(b[0], b[1], g[0], g[1]) > 400]
                if alive and b[5] > 0 and 0 < b[0] < WIDTH and 0 < b[1] < HEIGHT:
                    new_bullets.append(b)
            enemy_bullets = new_bullets

            new_traps = []
            for t in enemy_traps:
                t[2] -= 1
                if player.iframes == 0 and point_in_radius_sq(t[0], t[1], player.x, player.y, t[3] + pr):
                    if player.shield:
                        player.shield = False
                        particle_pool.spawn(player.x, player.y, (100,200,255), 12)
                    else:
                        player.hp -= 1; wave_damage_taken += 1; run_stats['damage_taken'] += 1
                        particle_pool.spawn(player.x, player.y, (255,50,50), 10, 'blood')
                        floating_numbers.spawn(player.x, player.y, "-1 ❤", (255, 80, 80), 28)
                        hit_stop.trigger(4)
                        if player.split_on_hit:
                            player.puddles.append([player.x, player.y, 600, 50])
                    player.iframes = int(60 * player.iframe_mult) + player.iframe_bonus
                elif t[2] > 0: new_traps.append(t)
            enemy_traps = new_traps

            # Power-ups with magnet
            new_powerups = []
            for p in powerups:
                if p.update():
                    # Magnet pull
                    if player.magnet:
                        dx = player.x - p.x; dy = player.y - p.y
                        d = math.sqrt(dx*dx + dy*dy)
                        if d < 200 and d > 0:
                            p.x += (dx / d) * 3; p.y += (dy / d) * 3
                    if point_in_radius_sq(p.x, p.y, player.x, player.y, p.radius + pr):
                        particle_pool.spawn(p.x, p.y, p.data['color'], 12)
                        n = p.data['name']
                        if n == 'health':
                            player.hp = min(player.max_hp, player.hp + 1)
                            particle_pool.spawn(player.x, player.y, (255,100,100), 10)
                            floating_numbers.spawn(player.x, player.y, "+1 ❤", (100, 255, 100), 24)
                        elif n == 'speed': player.buffs['speed'] = int(p.data['duration'] * player.power_duration_mult)
                        elif n == 'damage': player.buffs['damage'] = int(p.data['duration'] * player.power_duration_mult)
                        elif n == 'shield': player.shield = True
                        elif n == 'slowmo': player.buffs['slowmo'] = int(p.data['duration'] * player.power_duration_mult)
                        elif n == 'multiplier': player.buffs['multiplier'] = int(p.data['duration'] * player.power_duration_mult)
                        floating_numbers.spawn(p.x, p.y, n.upper(), p.data['color'], 22)
                    else: new_powerups.append(p)
            powerups = new_powerups

            particle_pool.update_all()
            floating_numbers.update_all()
            achievement_popup.update()
            combo_flash.update()
            wave_announcer.update()

            # --- Drawing ---
            for t in enemy_traps: pygame.draw.circle(screen, (150,50,50), (int(t[0]), int(t[1])), t[3], 2)
            for b in enemy_bullets:
                is_boss_bullet = any(e.is_boss for e in enemies)
                color = (255, 50, 50) if is_boss_bullet else (255, 100, 100)
                size = 8 if is_boss_bullet else 6
                pygame.draw.circle(screen, color, (int(b[0]), int(b[1])), size)
            for p in powerups: p.draw(screen)
            for v in villagers: v.draw(screen)
            for e in enemies: e.draw(screen)
            player.draw(screen)
            particle_pool.draw_all(screen)
            floating_numbers.draw_all(screen)

            if player.char_class == 'siren' and player.charm_active > 0:
                screen.blit(get_overlay_surface((255, 100, 150), 30), (0, 0))
            if player.buffs['slowmo'] > 0:
                screen.blit(get_overlay_surface((150, 100, 255), 20), (0, 0))

            draw_offscreen_indicators(screen, player, enemies)
            combo_flash.draw(screen)
            wave_announcer.draw(screen)
            achievement_popup.draw(screen)

            # --- UI ---
            wave_text = f"🌊 WAVE {current_wave}"
            if current_wave > 10: wave_text += " ∞"
            else: wave_text += f"/10"
            wave_color = GOLD if current_wave <= 10 else (150, 100, 255)
            draw_text(screen, wave_text, 24, 20, 20, wave_color)
            arch_icons = {'normal': '🌊', 'horde': '👥', 'elite': '⚔️', 'breather': '☕', 'boss': '💀'}
            draw_text(screen, f"{arch_icons.get(current_archetype, '🌊')} {current_archetype.upper()}", 16, 20, 50, wave_color)
            draw_text(screen, f"{DIFF_LABELS[selected_difficulty]} | {selected_class.title()}", 14, 20, 72, GRAY)

            heat_label, heat_color = adaptive_diff.get_heat_label()
            heat_bar_w = 80; heat_x = WIDTH - 20 - heat_bar_w; heat_y = 80
            draw_text(screen, f"Heat: {heat_label}", 12, heat_x, heat_y - 15, heat_color)
            pygame.draw.rect(screen, (50, 50, 60), (heat_x, heat_y, heat_bar_w, 6))
            heat_fill = min(1.0, adaptive_diff.heat / 2.0)
            pygame.draw.rect(screen, heat_color, (heat_x, heat_y, int(heat_bar_w * heat_fill), 6))
            pygame.draw.rect(screen, WHITE, (heat_x, heat_y, heat_bar_w, 6), 1)

            if wave_humans_total > 0:
                bar_w = 300; bar_h = 14
                bar_x = WIDTH//2 - bar_w//2; bar_y = 20
                pygame.draw.rect(screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h))
                progress = min(1.0, wave_humans_converted / wave_humans_total)
                fill_color = GOLD if current_wave <= 10 else (150, 100, 255)
                pygame.draw.rect(screen, fill_color, (bar_x, bar_y, int(bar_w * progress), bar_h))
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
                draw_text(screen, f"{wave_humans_converted}/{wave_humans_total}", 14, WIDTH//2, bar_y + bar_h + 10, WHITE, center=True)

            draw_text(screen, f"Score: {score}", 22, WIDTH-20, 20, GOLD)
            if combo > 1:
                cs = min(36, 24 + combo)
                cc = (255, 150+min(100,combo*10), 50)
                draw_text(screen, f"{combo}x COMBO!", cs, WIDTH-20, 50, cc)

            for i in range(player.max_hp):
                hi = get_heart_surface(emoji_mgr, 255 if i < player.hp else 50)
                if hi: screen.blit(hi, (WIDTH-100+i*30, 110))

            by = 140
            for buff_name, emoji_name in [('shield','shield'),('speed','lightning'),('damage','boom'),('slowmo','clock'),('multiplier','gem')]:
                val = player.shield if buff_name == 'shield' else player.buffs[buff_name]
                if val:
                    bi = emoji_mgr.get(emoji_name, 20)
                    if bi: screen.blit(bi, (WIDTH-30, by))
                    by += 25

            # Show owned upgrades count
            if player.upgrades:
                draw_text(screen, f"⬆️ {len(player.upgrades)}", 16, WIDTH-30, by + 5, GOLD)

            if daily_mode:
                draw_text(screen, "📅 DAILY CHALLENGE", 16, WIDTH//2, 60, GOLD, center=True)

            # --- Check wave completion ---
            wave_humans_remaining = sum(1 for v in villagers if not v.converted and v.alive)
            if wave_humans_remaining == 0 and len(enemies) == 0 and wave_humans_total > 0:
                complete_wave()
                state = STATE_WAVE_TRANSITION

            # --- Check player death ---
            if player.hp <= 0:
                # Second wind
                if player.second_wind and not player.second_wind_used:
                    player.second_wind_used = True
                    player.hp = 1
                    player.iframes = 120
                    combo_flash.trigger("💨 SECOND WIND! 💨", (150, 255, 255))
                    particle_pool.spawn(player.x, player.y, (150, 255, 255), 40)
                    hit_stop.trigger(15)
                # Phylactery
                elif player.phylactery and not player.phylactery_used:
                    player.phylactery_used = True
                    player.hp = player.max_hp
                    player.iframes = 120
                    combo_flash.trigger("💎 PHYLACTERY! 💎", (200, 80, 255))
                    particle_pool.spawn(player.x, player.y, (200, 80, 255), 50)
                    hit_stop.trigger(15)
                else:
                    death_message = random.choice(DEATH_MESSAGES)
                    run_stats['won'] = False
                    if current_wave > data.get('best_wave', 0):
                        data['best_wave'] = current_wave - 1
                    data['best_combo'] = max(data['best_combo'], best_combo)
                    data['best_score'] = max(data['best_score'], score)
                    data['total_criticals'] = data.get('total_criticals', 0) + run_stats.get('criticals', 0)
                    earned = check_achievements(data, run_stats)
                    for a in earned: achievement_popup.trigger(a)
                    save_data(data)
                    state = STATE_LOSE

        # =====================================================================
        # WIN
        # =====================================================================
        elif state == STATE_WIN:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            draw_text(screen, "🏆 VICTORY! 🏆", 60, WIDTH//2, 80, GOLD, center=True)
            draw_text(screen, f"Final Wave: {current_wave-1}", 32, WIDTH//2, 150, WHITE, center=True)
            draw_text(screen, f"Score: {score}", 36, WIDTH//2, 200, WHITE, center=True)
            draw_text(screen, f"Best Combo: {best_combo}x", 24, WIDTH//2, 250, (255, 150, 50), center=True)
            if player:
                draw_text(screen, f"Upgrades: {len(player.upgrades)}", 22, WIDTH//2, 290, (150, 200, 255), center=True)
            if HAS_CLIPBOARD:
                draw_text(screen, "Press [C] to copy score to clipboard", 18, WIDTH//2, 470, (100, 200, 255), center=True)
            draw_text(screen, "Press [R] / SPACE / ENTER to play again", 22, WIDTH//2, 510, WHITE, center=True)
            draw_text(screen, "Press [ESC] for main menu", 18, WIDTH//2, 540, GRAY, center=True)
            time_counter += 1

        # =====================================================================
        # LOSE
        # =====================================================================
        elif state == STATE_LOSE:
            offset = (time_counter // 2) % 40
            screen.blit(bg_surface, (-offset, -offset))
            draw_text(screen, "💀 DEFEATED 💀", 60, WIDTH//2, 70, RED, center=True)
            draw_text(screen, death_message, 22, WIDTH//2, 135, (255, 150, 150), center=True)
            draw_text(screen, f"Reached Wave {current_wave}", 32, WIDTH//2, 190, GOLD, center=True)
            draw_text(screen, f"Score: {score}", 32, WIDTH//2, 235, WHITE, center=True)
            draw_text(screen, f"Best Combo: {best_combo}x", 22, WIDTH//2, 275, (255, 150, 50), center=True)
            if player:
                draw_text(screen, f"Upgrades Collected: {len(player.upgrades)}", 20, WIDTH//2, 310, (150, 200, 255), center=True)
            best_wave = data.get('best_wave', 0); reached = current_wave - 1
            if reached > best_wave:
                draw_text(screen, "🎉 NEW WAVE RECORD! 🎉", 24, WIDTH//2, 345, GOLD, center=True)
            elif reached == best_wave:
                draw_text(screen, f"Tied your best wave ({best_wave})", 20, WIDTH//2, 345, GRAY, center=True)
            else:
                draw_text(screen, f"Best Wave: {best_wave}", 20, WIDTH//2, 345, GRAY, center=True)
            cls_best = data['high_scores'].get(selected_class, 0)
            draw_text(screen, f"Class Best Score: {cls_best}", 18, WIDTH//2, 380, GRAY, center=True)
            draw_text(screen, f"Overall Best Score: {data['best_score']}", 18, WIDTH//2, 405, GRAY, center=True)
            if HAS_CLIPBOARD:
                draw_text(screen, "Press [C] to copy score to clipboard", 18, WIDTH//2, 450, (100, 200, 255), center=True)
            draw_text(screen, "Press [R] / SPACE / ENTER to try again", 22, WIDTH//2, 490, WHITE, center=True)
            draw_text(screen, "Press [ESC] for main menu", 18, WIDTH//2, 520, GRAY, center=True)
            time_counter += 1

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()