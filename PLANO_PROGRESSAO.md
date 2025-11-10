# 🎮 PLANO: Sistema de Progressão Orgânica (Estilo Kenshi + Elden Ring)

**Data:** 2025-11-07
**Status:** ✅ FASE 1-3 IMPLEMENTADAS (MVP COMPLETO)
**Desenvolvedor:** Claude Code
**Para:** ChatGPT e equipe de desenvolvimento

---

## ✅ STATUS DE IMPLEMENTAÇÃO

### FASE 1: Sistema Base - ✅ COMPLETO
- ✅ 5 atributos adicionados ao Stats dataclass
- ✅ src/attributes.py criado com fórmulas balanceadas
- ✅ grant_xp() modificado para dar pontos
- ✅ Migração de save v1.3 implementada
- ✅ Sistema testado e funcionando

### FASE 2: UI Simples - ✅ COMPLETO
- ✅ src/ui/levelup_screen.py criado
- ✅ UI modal funcional com +/- buttons
- ✅ Preview de stats em tempo real
- ✅ Integrado no main loop
- ✅ Indicador pulsante no HUD

### FASE 3: Mecânicas Derivadas - ✅ COMPLETO
- ✅ Sistema de crítico (SKL) implementado
- ✅ Defesa multiplicativa (VIT + armor) implementada
- ✅ Bônus de gold (CHA) implementado
- ✅ Bônus de tropas (CHA) implementado
- ✅ Efeitos visuais (partículas douradas em crits)

### FASE 4: Equipment Scaling - ⏳ PENDENTE
- ⏳ Adicionar scaling grades às armas
- ⏳ Implementar requisitos de atributos
- ⏳ Soft lock com penalidade

### FASE 5: Polish - ⏳ PENDENTE
- ⏳ Painel de atributos detalhado no HUD
- ⏳ Preview completo na UI de level up
- ⏳ Tutorial/dicas

---

---

## 📋 CONTEXTO

### Problema Identificado:
O sistema atual de level up não é **sentido** pelo jogador:
- Level up atual: +2 ATK, +8 HP apenas
- Sem escolhas, sem impacto visível
- Progressão linear e previsível
- Equipamentos desconectados dos níveis
- Nenhum sistema de build/especialização

### Inspiração Solicitada:
- **Kenshi:** Progressão orgânica, stats aumentam com uso, sentida na prática
- **Elden Ring:** Distribuição de pontos de atributo, equipment scaling, level gates

### Objetivo:
Criar sistema de progressão **sentido e recompensador** SEM skill trees complexos.

---

## 🎯 SISTEMA PROPOSTO: Atributos + Equipment Scaling

### Conceito Core:
A cada level up, o jogador ganha **3 pontos de atributo** para distribuir livremente em 5 atributos principais. Cada atributo afeta múltiplos aspectos do gameplay de forma **imediatamente perceptível**.

---

## 📊 OS 5 ATRIBUTOS

### 1. **FORÇA (STR - Strength)**
**O que afeta:**
- ✅ **ATK:** +2 por ponto de STR
- ✅ **HP Max:** +2 por ponto de STR (além do bônus de VIT)
- ✅ **Weapon Scaling:** Armas pesadas (Machados, Espadas Grandes) escalam com STR

**Build ideal:** Guerreiro tanque que bate forte

---

### 2. **AGILIDADE (AGI - Agility)**
**O que afeta:**
- ✅ **SPD (Velocidade):** +3 pixels/segundo por ponto de AGI (base 180)
- ✅ **Stamina Regen:** +1% por ponto de AGI
- ✅ **Attack Speed:** Reduz cooldown de ataque em 1% por ponto de AGI
- ✅ **Weapon Scaling:** Armas leves (Adagas, Rapiers) escalam com AGI

**Build ideal:** Assassino rápido, hit-and-run

---

### 3. **RESISTÊNCIA (VIT - Vitality)**
**O que afeta:**
- ✅ **HP Max:** +8 por ponto de VIT
- ✅ **Stamina Max:** +2 por ponto de VIT
- ✅ **HP Regen:** +0.5 HP/segundo por ponto de VIT (fora de combate)
- ✅ **Defesa:** +1% de redução de dano por ponto de VIT (cap 30%)

**Build ideal:** Tank imortal, sobrevive tudo

---

### 4. **LIDERANÇA (CHA - Charisma)**
**O que afeta:**
- ✅ **Troop Stats Bonus:** +2% HP/ATK de tropas por ponto de CHA
- ✅ **Gold Find:** +5% gold drops por ponto de CHA
- ✅ **Recruitment Cost:** -2% custo de recrutar tropas por ponto de CHA
- ✅ **Shop Prices:** -1% preços de loja por ponto de CHA

**Build ideal:** General/Líder com exército forte

---

### 5. **TÉCNICA (SKL - Skill)**
**O que afeta:**
- ✅ **Crit Chance:** +1% por ponto de SKL (base 5%)
- ✅ **Crit Damage:** +5% por ponto de SKL (base 200%)
- ✅ **Block Power:** +2% redução ao bloquear por ponto de SKL (base 30%)
- ✅ **Parry Window:** +0.01s janela de parry perfeito por ponto de SKL (base 0.2s)

**Build ideal:** Combatente técnico, parries e críticos

---

## 🔢 FÓRMULAS DE STATS DERIVADOS

```python
# HP Max = 100 base + (VIT * 8) + (STR * 2)
hp_max = 100 + (vitality * 8) + (strength * 2)

# ATK = 10 base + (STR * 2) + (SKL * 0.5)
atk = 10 + (strength * 2) + (skill * 0.5)

# SPD = 180 base + (AGI * 3)
spd = 180 + (agility * 3)

# Stamina Max = 100 + (VIT * 2) + (AGI * 1)
stamina_max = 100 + (vitality * 2) + (agility * 1)

# Crit Chance = 5% base + (SKL * 1%)
crit_chance = 0.05 + (skill * 0.01)

# Block Power = 30% base + (SKL * 2%)
block_power = 0.30 + (skill * 0.02)

# Gold Bonus = 100% base + (CHA * 5%)
gold_bonus = 1.0 + (charisma * 0.05)

# Troop Bonus = CHA * 2%
troop_bonus = charisma * 0.02

# Defense = VIT * 1% (capped at 30%)
defense = min(0.30, vitality * 0.01)
```

---

## ⚔️ EQUIPMENT SCALING (Estilo Elden Ring)

### Conceito:
Cada arma tem **requisitos mínimos** de atributos e **scaling grades** (S/A/B/C/D/E) que determinam quanto dano extra ela ganha dos seus atributos.

### Scaling Grades:
- **S:** 100% do atributo convertido em dano bonus
- **A:** 80%
- **B:** 60%
- **C:** 40%
- **D:** 20%
- **E:** 10%

### Exemplos de Armas:

#### **Tier 1 - Early Game (Level 1-5)**
```python
Weapon(
    name="Iron Sword",
    damage=1.0,
    str_req=8,
    agi_req=5,
    scaling_str="C",  # 40% STR scaling
    scaling_agi="D"   # 20% AGI scaling
)

Weapon(
    name="Short Bow",
    damage=0.8,
    str_req=5,
    agi_req=10,
    scaling_str="E",  # 10% STR scaling
    scaling_agi="B"   # 60% AGI scaling
)
```

#### **Tier 2 - Mid Game (Level 6-15)**
```python
Weapon(
    name="Longsword",
    damage=1.4,
    str_req=15,
    agi_req=10,
    scaling_str="B",  # 60% STR scaling
    scaling_agi="C"   # 40% AGI scaling
)

Weapon(
    name="Rapier",
    damage=1.2,
    str_req=8,
    agi_req=18,
    scaling_str="E",  # 10% STR scaling
    scaling_agi="A"   # 80% AGI scaling
)
```

#### **Tier 3 - Late Game (Level 16+)**
```python
Weapon(
    name="Greatsword",
    damage=2.2,
    str_req=30,
    agi_req=5,
    scaling_str="S",  # 100% STR scaling
    scaling_agi="E"   # 10% AGI scaling
)

Weapon(
    name="Assassin's Blade",
    damage=1.8,
    str_req=10,
    agi_req=25,
    scaling_str="D",  # 20% STR scaling
    scaling_agi="S"   # 100% AGI scaling
)

Weapon(
    name="Quality Blade",
    damage=2.0,
    str_req=20,
    agi_req=20,
    scaling_str="A",  # 80% STR scaling
    scaling_agi="A"   # 80% AGI scaling
)
```

### Cálculo de Dano com Scaling:
```python
# Base damage from weapon
base_dmg = player.stats.atk * weapon.damage

# Scaling bonus from STR
str_scaling = {
    'S': 1.0, 'A': 0.8, 'B': 0.6, 'C': 0.4, 'D': 0.2, 'E': 0.1
}
str_bonus = player.stats.strength * str_scaling[weapon.scaling_str]

# Scaling bonus from AGI
agi_scaling = {
    'S': 1.0, 'A': 0.8, 'B': 0.6, 'C': 0.4, 'D': 0.2, 'E': 0.1
}
agi_bonus = player.stats.agility * agi_scaling[weapon.scaling_agi]

# Total scaling multiplier
scaling_multiplier = 1.0 + ((str_bonus + agi_bonus) / 100)

# Final damage
damage = base_dmg * scaling_multiplier * combo_mult
```

---

## 🎨 UI DE DISTRIBUIÇÃO DE PONTOS

### Tela que aparece após Level Up:

```
╔══════════════════════════════════════════════════════════════╗
║                   ⭐ LEVEL UP! ⭐                             ║
║                  You are now Level 5                         ║
║             You have 3 attribute points to spend             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  STRENGTH        [12] [+] [-]                                ║
║  ⚔️  ATK: 34 (+2)  ❤️  HP: +4                                ║
║  📦 Equipment: Greatsword (Requires 30 STR) ❌                ║
║                                                              ║
║  AGILITY         [10] [+] [-]                                ║
║  🏃 SPD: 210 (+3)  ⚡ Stamina Regen: +10%                    ║
║  📦 Equipment: Rapier (Requires 18 AGI) ❌                    ║
║                                                              ║
║  VITALITY        [15] [+] [-]                                ║
║  ❤️  HP Max: 250 (+8)  ⚡ Stamina Max: 130 (+2)              ║
║  🛡️  Defense: +15% damage reduction                          ║
║                                                              ║
║  CHARISMA        [8] [+] [-]                                 ║
║  💰 Gold Bonus: +40% (+5%)  👥 Troop Bonus: +16% (+2%)       ║
║  🏪 Shop Discount: -8% (-1%)                                 ║
║                                                              ║
║  SKILL           [10] [+] [-]                                ║
║  💥 Crit Chance: 15% (+1%)  🛡️  Block Power: 50% (+2%)       ║
║  ⏱️  Parry Window: 0.30s (+0.01s)                            ║
║                                                              ║
║                    Points Remaining: 3/3                     ║
║                                                              ║
║                       [CONFIRM]                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Funcionalidades:
- ✅ Botões [+] e [-] para adicionar/remover pontos ANTES de confirmar
- ✅ Preview em tempo real de como os stats vão mudar
- ✅ Mostra equipamentos que podem ser desbloqueados
- ✅ Indicador visual (❌ / ✅) de requisitos de equipamento
- ✅ Só pode confirmar quando todos os 3 pontos foram gastos
- ✅ ESC para cancelar e voltar (sem aplicar mudanças)

---

## 📈 EXEMPLOS DE BUILDS

### Build 1: GUERREIRO TANQUE
**Distribuição:** STR 35 / VIT 30 / Resto 10
```
Level 25:
- HP Max: 410 (massivo)
- ATK: 92 (muito alto)
- Defense: 30% (cap)
- Stamina Max: 160
- Usa: Greatsword (S scaling STR) = Dano absurdo
```

### Build 2: ASSASSINO RÁPIDO
**Distribuição:** AGI 40 / SKL 25 / Resto 10
```
Level 25:
- SPD: 300 (super rápido)
- Crit Chance: 30%
- Crit Damage: 325%
- Attack Speed: +40% faster
- Usa: Assassin's Blade (S scaling AGI) = Críticos devastadores
```

### Build 3: GENERAL/LÍDER
**Distribuição:** CHA 35 / VIT 25 / Resto 10
```
Level 25:
- Troop Bonus: +70% stats
- Gold Find: +175%
- Shop Discount: -35%
- HP: 360 (tanky o suficiente)
- Tropas são MUITO mais fortes que inimigos
```

### Build 4: BALANCED/QUALITY
**Distribuição:** STR 20 / AGI 20 / VIT 15 / SKL 15 / CHA 5
```
Level 25:
- Versátil em tudo
- Pode usar qualquer equipamento
- Sem fraquezas, sem forças extremas
- Usa: Quality Blade (A/A scaling) = Aproveitamento máximo
```

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### FASE 1: Sistema de Atributos Base (2-3h)

#### 1.1 Modificar Stats Dataclass
**Arquivo:** `src/entities.py`

```python
@dataclass
class Stats:
    # Stats base (já existentes)
    hp_max: float
    hp: float
    atk: float
    spd: float
    level: int
    xp: int
    xp_to_next_level: int = 10
    food: int = 20
    gold: int = 0

    # NOVOS: Atributos primários
    strength: int = 10      # Força
    agility: int = 10       # Agilidade
    vitality: int = 10      # Resistência
    charisma: int = 10      # Liderança
    skill: int = 10         # Técnica
    attribute_points: int = 0  # Pontos disponíveis

    # NOVOS: Stats derivados (calculados)
    stamina_max: float = 100.0
    crit_chance: float = 0.05
    crit_damage: float = 2.0
    block_power: float = 0.3
    gold_bonus: float = 1.0
    troop_bonus: float = 0.0
    defense: float = 0.0
    parry_window: float = 0.2
```

#### 1.2 Modificar grant_xp()
**Arquivo:** `src/rpg.py`

```python
def grant_xp(player, amount: int) -> Dict[str, Any]:
    """Grant XP to player and handle level-ups."""
    leveled = False
    points_earned = 0

    player.stats.xp += int(max(0, amount))

    # Level-up loop
    while player.stats.xp >= xp_for_level(player.stats.level + 1):
        player.stats.level += 1
        player.stats.attribute_points += 3  # MUDANÇA: Dar 3 pontos
        points_earned += 3

        # HP restored to max (recalculated by attributes)
        from src.attributes import calculate_derived_stats
        calculate_derived_stats(player)
        player.stats.hp = player.stats.hp_max

        # Update xp_to_next_level
        player.stats.xp_to_next_level = xp_for_level(player.stats.level + 1)
        leveled = True

    return {
        "leveled_up": leveled,
        "points_earned": points_earned
    }
```

#### 1.3 Criar Sistema de Derivação
**Novo arquivo:** `src/attributes.py`

```python
"""Attribute system - Calculate derived stats from primary attributes."""

def calculate_derived_stats(player):
    """Recalculate all derived stats from primary attributes."""
    STR = player.stats.strength
    AGI = player.stats.agility
    VIT = player.stats.vitality
    CHA = player.stats.charisma
    SKL = player.stats.skill

    # HP Max = 100 base + (VIT * 8) + (STR * 2)
    player.stats.hp_max = 100 + (VIT * 8) + (STR * 2)

    # ATK = 10 base + (STR * 2) + (SKL * 0.5)
    player.stats.atk = 10 + (STR * 2) + (SKL * 0.5)

    # SPD = 180 base + (AGI * 3)
    player.stats.spd = 180 + (AGI * 3)

    # Stamina Max = 100 + (VIT * 2) + (AGI * 1)
    player.stats.stamina_max = 100 + (VIT * 2) + (AGI * 1)

    # Crit Chance = 5% base + (SKL * 1%)
    player.stats.crit_chance = 0.05 + (SKL * 0.01)

    # Crit Damage = 200% base + (SKL * 5%)
    player.stats.crit_damage = 2.0 + (SKL * 0.05)

    # Block Power = 30% base + (SKL * 2%)
    player.stats.block_power = 0.30 + (SKL * 0.02)

    # Gold Bonus = 100% base + (CHA * 5%)
    player.stats.gold_bonus = 1.0 + (CHA * 0.05)

    # Troop Bonus = CHA * 2%
    player.stats.troop_bonus = CHA * 0.02

    # Defense = VIT * 1% (capped at 30%)
    player.stats.defense = min(0.30, VIT * 0.01)

    # Parry Window = 0.2s base + (SKL * 0.01s)
    player.stats.parry_window = 0.2 + (SKL * 0.01)


def calculate_weapon_scaling(player, weapon) -> float:
    """Calculate damage multiplier from weapon scaling."""
    scaling_values = {
        'S': 1.0,
        'A': 0.8,
        'B': 0.6,
        'C': 0.4,
        'D': 0.2,
        'E': 0.1
    }

    str_scaling = scaling_values.get(weapon.scaling_str, 0.0)
    agi_scaling = scaling_values.get(weapon.scaling_agi, 0.0)

    str_bonus = player.stats.strength * str_scaling
    agi_bonus = player.stats.agility * agi_scaling

    # 1.0 = base, + bonus from scaling
    multiplier = 1.0 + ((str_bonus + agi_bonus) / 100)

    return multiplier


def can_equip_weapon(player, weapon) -> bool:
    """Check if player meets weapon requirements."""
    str_req = getattr(weapon, 'str_req', 0)
    agi_req = getattr(weapon, 'agi_req', 0)

    return (player.stats.strength >= str_req and
            player.stats.agility >= agi_req)
```

---

### FASE 2: UI de Distribuição (1-2h)

**Novo arquivo:** `src/ui/levelup_screen.py`

```python
"""Level-up attribute distribution screen."""

import pygame
from src.ui_components import Panel, UIColors
from src.attributes import calculate_derived_stats

class LevelUpScreen:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.temp_attrs = {
            'strength': player.stats.strength,
            'agility': player.stats.agility,
            'vitality': player.stats.vitality,
            'charisma': player.stats.charisma,
            'skill': player.stats.skill
        }
        self.points_spent = 0
        self.max_points = player.stats.attribute_points

    def run(self):
        """Run the level-up screen loop until player confirms."""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False  # Cancel

                if event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.handle_click(event.pos)
                    if result == "confirm":
                        self.apply_attributes()
                        return True

            self.render()
            pygame.display.flip()
            clock.tick(60)

    def handle_click(self, pos):
        """Handle button clicks for +/- and Confirm."""
        # Implementation of click handling for +/- buttons
        pass

    def apply_attributes(self):
        """Apply temporary attributes to player."""
        self.player.stats.strength = self.temp_attrs['strength']
        self.player.stats.agility = self.temp_attrs['agility']
        self.player.stats.vitality = self.temp_attrs['vitality']
        self.player.stats.charisma = self.temp_attrs['charisma']
        self.player.stats.skill = self.temp_attrs['skill']
        self.player.stats.attribute_points = 0

        calculate_derived_stats(self.player)

    def render(self):
        """Render the level-up screen."""
        # Dark overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Main panel
        panel_width = 600
        panel_height = 500
        panel_x = (self.screen.get_width() - panel_width) // 2
        panel_y = (self.screen.get_height() - panel_height) // 2

        panel = Panel(panel_x, panel_y, panel_width, panel_height,
                     title="LEVEL UP!", border_color=(255, 215, 0))
        panel.render(self.screen)

        # Render attribute rows
        # ... (implementation details)
```

---

### FASE 3: Equipment Scaling (1h)

#### 3.1 Modificar Weapon Dataclass
**Arquivo:** `src/equipment.py`

```python
@dataclass
class Weapon:
    name: str
    damage: float
    cooldown: float
    stamina_cost: float
    range: float
    value: int

    # NOVOS: Requirements e Scaling
    str_req: int = 0
    agi_req: int = 0
    scaling_str: str = "E"  # S/A/B/C/D/E
    scaling_agi: str = "E"
```

#### 3.2 Atualizar Database de Armas
**Arquivo:** `src/equipment.py` - função `get_all_weapons()`

Adicionar requisitos e scaling a todas as 30+ armas existentes.

#### 3.3 Modificar Cálculo de Dano
**Arquivo:** `src/battle_combat.py` - linha 132

```python
# OLD:
damage = (battle.player.stats.atk * weapon.damage) * combo_mult

# NEW:
from src.attributes import calculate_weapon_scaling

weapon = battle.player.equipment.get_weapon()
scaling_mult = calculate_weapon_scaling(battle.player, weapon)
base_damage = battle.player.stats.atk * weapon.damage
damage = (base_damage * scaling_mult) * combo_mult
```

---

### FASE 4: Mecânicas Derivadas (1h)

#### 4.1 Sistema de Crítico
**Arquivo:** `src/battle_combat.py` - apply_player_attack_damage()

```python
import random

# After calculating base damage
if random.random() < battle.player.stats.crit_chance:
    damage *= battle.player.stats.crit_damage
    vfx.create_crit_effect(enemy.pos)
    color = (255, 215, 0)  # Gold for crit
    battle_effects.add_damage_number(battle, enemy.pos[0], enemy.pos[1],
                                     int(damage), color)
else:
    # Normal damage number
    battle_effects.add_damage_number(battle, enemy.pos[0], enemy.pos[1],
                                     int(damage), (255, 255, 100))
```

#### 4.2 Defense System
**Arquivo:** `src/battle_combat.py` - apply_enemy_attack_damage()

```python
# Apply defense before damage
damage *= (1.0 - target.stats.defense)
```

#### 4.3 Troop Leadership Bonuses
**Arquivo:** `src/battle.py` - __init__()

```python
# When initializing troops in battle
for troop in troops:
    troop.stats.hp_max *= (1.0 + player.stats.troop_bonus)
    troop.stats.atk *= (1.0 + player.stats.troop_bonus)
    troop.stats.hp = troop.stats.hp_max
```

#### 4.4 Gold Bonus
**Arquivo:** `main.py` - battle rewards

```python
gold_gained = result.get("gold", 0)
gold_gained = int(gold_gained * player.stats.gold_bonus)
player.stats.gold += gold_gained
```

---

### FASE 5: Feedback Visual (30min)

#### 5.1 Indicador de Pontos Disponíveis
**Arquivo:** `src/ui/hud.py`

```python
# Se tem pontos para gastar, mostrar indicador pulsante
if player.stats.attribute_points > 0:
    pulse = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.005)
    font_size = int(24 * pulse)
    font = pygame.font.Font(None, font_size)
    text = font.render(f"POINTS TO SPEND: {player.stats.attribute_points}",
                      True, (255, 215, 0))
    screen.blit(text, (screen_width // 2 - text.get_width() // 2, 10))
```

#### 5.2 Efeito Visual de Crítico
**Arquivo:** `src/vfx.py`

```python
def create_crit_effect(pos):
    """Create golden particles for critical hit."""
    for i in range(30):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 5)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = random.uniform(0.5, 1.0)
        size = random.uniform(3, 6)
        color = (255, 215, 0)  # Gold
        add_particle(Particle(list(pos), vel, lifespan, color, size))
```

---

### FASE 6: Integração no Main Loop (30min)

**Arquivo:** `main.py`

```python
# Após battle victory e grant_xp
level_up_result = rpg.grant_xp(player, int(gained * max(1.0, diff)))

if level_up_result.get("leveled_up", False):
    vfx.create_levelup_glow(player.pos)
    menus.show_notification(screen, f"LEVEL UP! Now Level {player.stats.level}!",
                           duration=2.5, color=(255, 215, 0))

    # Se tem pontos para gastar, abrir tela de level up
    if player.stats.attribute_points > 0:
        from src.ui.levelup_screen import LevelUpScreen
        levelup_screen = LevelUpScreen(screen, player)
        confirmed = levelup_screen.run()

        if confirmed:
            menus.show_notification(screen, "Attributes updated!",
                                   duration=1.5, color=(100, 255, 100))
```

---

## 📊 BALANCEAMENTO

### XP Requirements (Mantido Linear):
```
Level 1→2: 20 XP
Level 5→6: 60 XP
Level 10→11: 110 XP
Level 20→21: 210 XP
```

### Pontos de Atributo por Nível:
```
Level 1: 50 pontos base (10 em cada atributo)
Level 5: 62 pontos total (50 + 12)
Level 10: 77 pontos total (50 + 27)
Level 20: 107 pontos total (50 + 57)
```

### Exemplo de Progressão (Pure STR Build):
```
Level 1:  STR 10 → ATK 30,  HP 120
Level 5:  STR 22 → ATK 54,  HP 164
Level 10: STR 37 → ATK 84,  HP 224
Level 20: STR 67 → ATK 144, HP 344

Dano percebido aumenta 380% (de 30 para 144 ATK)!
```

---

## 🔄 COMPATIBILIDADE COM SAVES ANTIGOS

### Migração Automática:
**Arquivo:** `src/save_system.py`

```python
def _migrate_save_data(save_data: dict) -> dict:
    """Migrate old saves to new version."""

    # Se save não tem atributos, criar com valores padrão
    if "strength" not in save_data.get("player", {}).get("stats", {}):
        player_stats = save_data["player"]["stats"]
        level = player_stats.get("level", 1)

        # Distribuir pontos baseado no nível
        # Level 1 = 10 em cada, Level 5 = 10 + (4*3) = 22 pontos
        base_attr = 10
        total_points = (level - 1) * 3

        # Distribuir igualmente (balanced build)
        points_per_attr = total_points // 5
        remainder = total_points % 5

        player_stats["strength"] = base_attr + points_per_attr + (1 if remainder > 0 else 0)
        player_stats["agility"] = base_attr + points_per_attr + (1 if remainder > 1 else 0)
        player_stats["vitality"] = base_attr + points_per_attr + (1 if remainder > 2 else 0)
        player_stats["charisma"] = base_attr + points_per_attr + (1 if remainder > 3 else 0)
        player_stats["skill"] = base_attr + points_per_attr + (1 if remainder > 4 else 0)
        player_stats["attribute_points"] = 0

        # Recalcular stats derivados será feito ao carregar

    return save_data
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Sistema Base
- [ ] Adicionar 5 atributos ao Stats dataclass
- [ ] Modificar grant_xp() para dar pontos em vez de stats fixos
- [ ] Criar src/attributes.py com cálculo de stats derivados
- [ ] Testar cálculos de stats derivados

### Fase 2: UI
- [ ] Criar src/ui/levelup_screen.py
- [ ] Implementar tela modal de distribuição
- [ ] Adicionar preview de stats em tempo real
- [ ] Testar botões +/- e confirmação

### Fase 3: Equipment
- [ ] Adicionar str_req, agi_req, scaling_str, scaling_agi ao Weapon
- [ ] Atualizar database de 30+ armas com requisitos
- [ ] Implementar calculate_weapon_scaling()
- [ ] Modificar cálculo de dano para usar scaling
- [ ] Adicionar checks de requisitos na loja

### Fase 4: Mecânicas
- [ ] Implementar sistema de crítico (SKL)
- [ ] Implementar sistema de defesa (VIT)
- [ ] Implementar bônus de liderança (CHA)
- [ ] Implementar bônus de gold (CHA)
- [ ] Testar todos os bônus derivados

### Fase 5: Visual
- [ ] Adicionar indicador de pontos disponíveis no HUD
- [ ] Criar efeito visual de crítico (partículas douradas)
- [ ] Melhorar notificação de level up
- [ ] Testar feedback visual

### Fase 6: Integração
- [ ] Integrar levelup_screen no main loop
- [ ] Adicionar migração de saves antigos
- [ ] Testar compatibilidade com saves existentes
- [ ] Balancear requisitos de equipamentos

### Fase 7: Testes
- [ ] Testar todas as 4 builds (STR, AGI, CHA, Balanced)
- [ ] Verificar balanceamento de dano
- [ ] Confirmar que level ups são SENTIDOS
- [ ] Ajustar fórmulas se necessário

---

## 🎯 RESULTADO ESPERADO

### Antes (Sistema Atual):
```
Level 1 → Level 5:
- ATK: 12 → 20 (+8, +66%)
- HP: 100 → 132 (+32, +32%)
- Sem escolhas, sem especialização
```

### Depois (Sistema Proposto):
```
Level 1 → Level 5 (Pure STR Build):
- STR: 10 → 22 (+12)
- ATK: 30 → 54 (+24, +80%)
- HP: 120 → 164 (+44, +37%)
- Pode usar armas Tier 2 (req 15 STR) ✅
- Sente MUITO mais forte

Level 1 → Level 5 (Pure AGI Build):
- AGI: 10 → 22 (+12)
- SPD: 210 → 246 (+36, +17% mais rápido)
- Stamina Regen: +22%
- Ataca 22% mais rápido
- Sente MUITO mais ágil
```

---

## 📝 NOTAS FINAIS

### Filosofia do Design:
1. **Simplicidade:** 5 atributos claros, sem complexidade desnecessária
2. **Escolhas Significativas:** Cada ponto gasto é SENTIDO imediatamente
3. **Build Diversity:** 4+ builds viáveis, cada um com gameplay diferente
4. **Sem Skill Trees:** Progressão direta, sem menus complexos
5. **Estilo Elden Ring:** Distribuição livre, equipment scaling, level gates

### Inspirações:
- **Elden Ring:** Sistema de atributos, weapon scaling (S/A/B/C/D/E)
- **Kenshi:** Progressão orgânica, stats que afetam gameplay diretamente
- **Dark Souls:** Equipment requirements, build diversity

### Próximos Passos Após Implementação:
1. Adicionar mais armas especializadas (pure STR, pure AGI, quality)
2. Considerar adicionar armaduras com requisitos de atributos
3. Adicionar soft caps (ex: STR acima de 40 rende menos retorno)
4. Possível sistema de respec (resetar atributos) por gold

---

**FIM DO PLANO**

🎮 Sistema pronto para implementação! 🎮
