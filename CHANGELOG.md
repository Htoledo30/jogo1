# Changelog
## Mount & Blade 2D RPG - Development Log

---

## v0.9.3 - Sprites (Player + Buildings), Arena Wiring, Overworld Tuning — 2025-11-09

Added
- Player battle sprite (Tiny Swords Blue Warrior Idle) only in arenas.
- World building sprites (Tiny Swords Buildings):
  - Castle → Castle.png (ally=Blue, neutral=Black, enemy=Red), bandit camps always Yellow.
  - Town → House1.png (colored by relation).
  - Bandit Camp → Tower.png (Yellow) — doubled visual size.
- New modules to de-tangle responsibilities:
  - `src/sprite_manager.py` (spritesheet loader + cache)
  - `src/animation.py` (Animation + AnimationController scaffold)
  - `src/battle_sprites.py` (battle-only player sprite drawing)
  - `src/world_sprites.py` (overworld building sprites by relation/type)

Changed
- `src/battle_rendering.py`: delegates player drawing to `battle_sprites`.
- `src/world.py` + `main.py`: `render_world` now receives `player_relations` to color buildings by relation.
- Interaction radius tuned (closer to building center):
  - Castle ≈ 65% of `loc.radius`, Town/Camp ≈ 60% (with minimums).
- Anchoring for buildings switched to center-center (sprite center aligns to interaction center) for consistent “Press E” feel.

Fixed
- Shadow black square under sprites: `vfx.draw_entity_shadow` now uses normal alpha blending (no MULT), removing rectangle darkening.

Notes
- Overworld visuals updated; minimap icons remain simple for readability (can be swapped later).
- Battle player sprite scale factor available in `battle_sprites.py` for quick tuning.


## v0.9.2 - Claude: Sistema de Tropas (Mount & Blade) + Refatoração de Batalha — 2025-11-07

Fase 1 — Sistema de Tropas (Overworld estilo Mount & Blade)
- src/world.py:574-579 Desabilitada renderização de tropas no overworld (comentado) para manter tropas visíveis apenas em batalha.
- src/world.py:642-645 Desabilitada renderização de tropas no minimapa (comentado) pelo mesmo motivo.
- src/ui/hud.py:41 Adicionado parâmetro `troops_list` em `draw_hud(...)`.
- src/ui/hud.py:88-139 Novo painel de informações de tropas (apenas no overworld): contagem por tipo (warriors/archers/tanks) e base para HP médio.
- main.py:384 Passa `troops_list=player_troops` ao HUD no overworld.
- main.py:459 Passa `troops_list=player_troops` ao HUD durante a batalha (HUD usa para contagem).

Fase 2 — Refatoração de battle.py (responsabilidades separadas)
- src/battle_rendering.py (novo): renderização completa (battle, UI, entidades, tropas, indicadores de ataque).
- src/battle_systems.py (novo): formação (circle/line/wedge), redistribuição de alvos, terreno elevado, promoções e modificadores de terreno.
- src/battle_ai_enhanced.py (novo): IA com prioridade por score, bloqueio com timing, estados (CHASING/BLOCKING/FLEEING/RETREATING), movimento com circling/spacing e clamp de arena.
- src/battle_combat.py (novo): processamento de ataque do player, dano com combos, ataques de tropas melee, início/dano de ataques inimigos (com blocking mechanics).
- src/battle.py: adicionados imports para os novos módulos e delegação das responsabilidades.

Notas
- Estes ajustes alinham a visibilidade e o fluxo de tropas ao estilo Mount & Blade: mapa limpo, tropas entram “em cena” apenas na arena.
- A refatoração facilita manutenção, testes e evolução futura (IA/efeitos/sistemas separados).

## v0.9.1 - IA de Arqueiros + Projéteis com Times (ChatGPT) — 2025-11-07

### Added
- Mira preditiva para arqueiros (inimigos e tropas) usando estimativa de velocidade do alvo via `prev_positions` e `_last_dt`.
- Checagem simples de linha de tiro: evita disparo se houver aliado no caminho até o alvo.
- `ProjectileManager` agora suporta `team` ("ally" | "enemy") para acertar apenas o lado oposto.

### Changed
- Inimigos arqueiros disparam com `team="enemy"`; tropas arqueiras com `team="ally"`.
- `BattleController.update()` passa a expor `self._last_dt` para auxiliar a mira preditiva.

### Files
- `src/battle_ai.py`: mira preditiva + linha de tiro para inimigos arqueiros.
- `src/battle_troop_ai.py`: mira preditiva + linha de tiro para tropas arqueiras.
- `src/battle_projectiles.py`: refeito com suporte a `team` e colisão por lado.
- `src/battle.py`: armazena `_last_dt` para consumo dos módulos auxiliares.

### Notes
- Mantido limite de projéteis (60) para estabilidade.
- Próximos: rios/estradas curvos, bônus de estrada, comparação de itens no inventário, micro-otimizações de distância.

## v0.9 - Facções, Castelos e Patrulhas (ChatGPT) — 2025-11-06

### Added
- Facções centralizadas em `src/factions.py` com pesos de Loja/Loot/Spawn e helpers (`roll_shop_items`, `roll_enemy_type`, `roll_loot`).
- Castelos por facção adicionados ao mundo (`src/world.py`), um para cada: Macedon, Greeks, Ptolemaic, Seleucid, Rome, Carthage, Kush, Maurya, Pontus, Thrace.
- Patrulhas periódicas saindo de cada castelo com limite de densidade local.
- Loja por facção: `equipment.get_random_shop_inventory(faction_id=...)` usa o estoque temático via `factions.roll_shop_items`.
- Loot por facção após batalha via `factions.roll_loot` baseado na facção do encontro.

### Changed
- Spawns iniciais/respawns agora são ancorados aos castelos; cada inimigo recebe `e.faction` e arquétipo conforme facção.
- Encontros (`world.update_world`) agora carregam a facção do inimigo em vez de `bandits` fixo.
- Tela de Loja usa `CURRENT_SHOP_FACTION_ID` derivado da localização.
- Combate usa atributos da arma equipada para `range`, `cooldown` e `stamina_cost`.

### Fixed
- Tooltip NameError (gerador ajustado).
- Callbacks de inventário (equip/drop) usando `Item` corretamente.
- Números de dano duplicando durante um mesmo swing (tracking por inimigo atingido).
- Patrulhas sem `chase_alert_cooldown` (agora inicializado e atualizado com `getattr`).

### Notes
- Conteúdo histórico 280 a.C. expandido (armas/armaduras/arcos/escudos) e mapeamentos de `equip_item` para IDs legados do combate.
