n# ⚔️ Mount & Blade 2D RPG ⚔️

Um jogo 2D de mundo aberto inspirado em **Mount & Blade**, com elementos de **Rome: Total War** e **Kenshi**, desenvolvido em Python + Pygame.

**Desenvolvido por:** Claude, ChatGPT & Gemini
**Testado por:** Você! (e por nós, as IAs)

---

## 🚀 Instalação Rápida

### 1. Instalar o Jogo

Clique 2x no arquivo:
```
install.bat
```

Isso vai:
- Verificar se Python está instalado
- Atualizar pip
- Instalar Pygame automaticamente

### 2. Rodar o Jogo

Clique 2x no arquivo:
```
run.bat
```

Ou no terminal:
```bash
python main.py
```

---

## 🎮 Controles

### Mundo Aberto (Overworld)
- **WASD / Setas:** Mover o personagem.
- **E:** Entrar em cidades/locais próximos.
- **ESC:** Sair do jogo ou de menus.
- **I:** Abrir/Fechar inventário.

### Batalha
- **WASD / Setas:** Mover o personagem.
- **Mouse:** Mirar.
- **Click Esquerdo:** Atacar na direção do mouse.
- **Shift / Click Direito:** Bloquear ataques.
- **1, 2, 3:** Mudar a formação das tropas (Círculo, Linha, Cunha).
- **ESC:** Pausar o jogo.

### Menus
- **W/S / Setas:** Navegar entre as opções.
- **Enter / Espaço / E:** Selecionar opção.

### Escravidão
- **Espaço (repetidamente):** Tentar escapar.

---

## 📖 Como Jogar

### Objetivo
Explore um mundo vasto, recrute um exército, gerencie suas tropas e facções, e conquiste seus inimigos em batalhas táticas.

### Mecânicas de Jogo

#### 1. Exploração (Estilo Mount & Blade)
- **Mundo Aberto:** Explore um mapa de 4000x3000 com uma câmera que segue o jogador.
- **Localizações:** Entre em cidades, castelos e acampamentos de bandidos para interagir.
- **Recrutamento:** Contrate tropas em cidades e castelos para aumentar seu exército.
- **Tropas no Mapa:** Suas tropas te seguem em formação pelo mundo.
- **Minimapa:** Navegue pelo mundo usando o minimapa no canto superior direito.
- **Efeitos Visuais:** Poeira ao mover, rastro de arma, sangue ao acertar, faíscas ao bloquear e brilho ao subir de nível.

#### 2. Combate Tático (Estilo Mount & Blade)
- **Combate Direcional:** Ataque na direção do seu mouse.
- **Bloqueio e Parry:** Reduza o dano bloqueando ou execute um "Parry Perfeito" para anular o dano e atordoar o inimigo.
- **Stamina:** Gerencie sua estamina, que é consumida ao atacar e bloquear.
- **Sistema de Combo:** Aumente seu dano acertando ataques em sequência.

#### 3. Gerenciamento e RPG (Estilo Mount & Blade)
- **Sistema de Equipamentos:** Compre e encontre armas e armaduras que melhoram seus atributos. Gerencie seus itens na tela de inventário.
- **Progressão:** Ganhe XP e ouro ao vencer batalhas para subir de nível e recrutar mais tropas.
- **Diplomacia:** Suas ações afetam sua relação com as facções (Reino, Bandidos). Estar em guerra com uma facção impede o acesso às suas cidades.

#### 3. Estratégia (Estilo Rome: Total War)
- **Formações de Batalha:** Comande suas tropas para formar um Círculo, Linha ou Cunha durante o combate.
- **Tipos de Unidade:** Recrute 4 tipos de tropas: Infantaria, Arqueiros, Cavalaria e Tanques.
- **Vantagem de Terreno:** Ganhe bônus de ataque e defesa ao lutar em terreno elevado (colinas).

#### 5. Sobrevivência e Consequências (Estilo Kenshi)
- **Sistema de Fome:** Você e suas tropas consomem comida. Ficar sem rações causa perda de vida. Compre comida nas cidades.
- **Escravidão:** Se for derrotado por bandidos, há uma chance de ser capturado, perder ouro, tropas e precisar escapar através de um mini-game.

---

## 🏗️ Estrutura do Projeto

```
jogo rpg/
├── main.py              # Game loop principal
├── requirements.txt     # Dependências (Pygame)
├── install.bat         # Script de instalação
├── run.bat             # Script para rodar o jogo
├── README.md           # Este arquivo (você está aqui)
├── COMMUNICATION.md    # Canal de comunicação da equipe
├── CHANGELOG.md        # Histórico de versões do projeto
├── ARCHITECTURE.md     # Documentação da arquitetura técnica
├── index.html          # Dashboard visual do projeto (abra no navegador)
│
└── src/                # Código fonte
    ├── entities.py     # Definições de Player, inimigos, tropas e seus stats
    ├── rpg.py          # Lógica de XP, level up e dificuldade
    ├── world.py        # Geração e gerenciamento do mundo, encontros e câmera
    ├── battle.py       # Sistema de combate tático em arena
    ├── equipment.py    # Definições de equipamentos (armas, armaduras)
    ├── vfx.py          # Sistema de efeitos visuais e partículas
    ├── save_system.py  # Lógica para salvar e carregar o progresso do jogo
    ├── items.py        # Definições de itens genéricos e tipos
    ├── factions.py     # Facções centralizadas (loja/loot/spawn)
    ├── item_bridge.py  # Funções de conversão entre itens e equipamentos
    ├── inventory_ui_v2.py # Interface de usuário para o inventário
    ├── ui_components.py # Componentes reutilizáveis de UI (botões, painéis, etc.)
    └── ui_shop.py      # Interface de usuário para a loja
```

---

---

## ✨ Novidades v1.1 (2025-11-07) - MELHORIAS CRÍTICAS

### 🚀 Infraestrutura Profissional Implementada:
- ✅ **Sistema de Logging** - Debug fácil com logs detalhados (`logs/`)
- ✅ **Memory Leak Corrigido** - VFX object pooling implementado
- ✅ **Resource Manager** - Cache de fontes/assets (+40-50% FPS)
- ✅ **Save System Robusto** - Backup automático + validação
- ✅ **150+ Constantes Organizadas** - Balanceamento centralizado
- ✅ **Exception Handling** - Errors específicos, não mais silenciados

**📖 Leia:** [`IMPROVEMENTS_FINAL.md`](IMPROVEMENTS_FINAL.md) para detalhes técnicos completos.

---

## Status Atual (v0.9)

### Novidades v0.9.3 (2025-11-09)
- Player em batalha usa sprite do Tiny Swords (Blue Warrior Idle), mantendo overworld separado.
- Edifícios no overworld usam sprites do Tiny Swords/Buildings por relação (ally=Blue, neutral=Black, enemy=Red; bandits=Yellow):
  - Castle → Castle.png; Town → House1.png; Bandit Camp → Tower.png (tamanho dobrado)
- Ancoragem centrada no loc.pos para alinhar com raio de interação (Press E).
- Raio de interação/descoberta reduzido (castle≈0.65×radius; town/camp≈0.60×radius) para evitar acesso de muito longe.
- Sombra corrigida (sem quadrado preto): alpha normal em vfx.draw_entity_shadow.

Arquivos novos: src/sprite_manager.py, src/animation.py, src/battle_sprites.py, src/world_sprites.py.

### Implementado pelo ChatGPT
- [x] Game loop 60 FPS
- [x] Movimentação do player (WASD)
- [x] Overworld com grid visual
- [x] Inimigos que vagam pelo mapa
- [x] Colisão que inicia batalhas
- [x] Sistema de XP e level up
- [x] HUD com HP e nível
- [x] Dificuldade que escala com tempo

### Novidades
- Sistema de facções centralizado (loja/loot/spawn) em `src/factions.py`.
- Castelos por facção e patrulhas periódicas saindo dos castelos.
- Spawns ancorados em castelos (distribuição temática por região).
- Lojas de castelo vendem itens da facção; loot pós-batalha por facção.
- Combate usa atributos da arma (`range`, `cooldown`, `stamina_cost`).

### Futuro (Fases 2-7)
- [ ] Combate direcional estilo Mount & Blade
- [ ] Inventário e equipamentos
- [ ] Sistema de facções
- [ ] Mundo maior com cidades
- [ ] Quests e NPCs
- [ ] Companheiros e party
- [ ] Pixel art assets
- [ ] Sons e música

---

## Troubleshooting

### "Python não encontrado"
**Solução:** Instale Python 3.11 ou 3.12 de https://www.python.org/downloads/
**IMPORTANTE:** Marque "Add Python to PATH" durante instalação!

### IMPORTANTE: Python 3.14 NÃO é compatível!
**Problema:** Pygame ainda não tem builds para Python 3.14 (muito novo)
**Solução:** Você precisa instalar Python 3.12.x
1. Desinstale Python 3.14
2. Baixe Python 3.12 de https://www.python.org/downloads/
3. Instale marcando "Add Python to PATH"
4. Execute `install.bat` novamente

### "Pygame não instalado"
**Solução:** Execute `install.bat` ou rode manualmente:
```bash
python -m pip install pygame
```

### "Erro ao importar pygame"
**Solução:** Reinstale com:
```bash
python -m pip uninstall pygame
python -m pip install pygame
```

### Tela preta / Jogo não abre
**Solução:**
1. Verifique se tem erros no terminal
2. Tente rodar via terminal: `python main.py`
3. Veja os erros que aparecem

### FPS baixo / Lento
**Solução:**
- Feche outros programas
- Seu PC pode estar com poucos recursos

---

## Desenvolvimento

### Para Desenvolvedores

Este projeto é desenvolvido colaborativamente por três IAs:
- **Claude:** Sistema de batalha, core engine
- **ChatGPT:** World, entities, RPG systems
- **Gemini:** Otimização, IA avançada, geração procedural

**Documentação de Dev:**
- `docs/index.html` - Dashboard visual (abra no navegador)
- `docs/COMMUNICATION.md` - Coordenação entre devs
- `docs/ARCHITECTURE.md` - Design técnico

---

## Versão

**v0.1-MVP** (2025-11-04)
- Primeira versão jogável
- Sistema de batalha placeholder
- Overworld funcional
- Sistema de progressão básico

---

## Licença

Este é um projeto experimental desenvolvido por IAs para fins educacionais.

---

## Feedback

Como tester, reporte bugs e sugestões para os desenvolvedores (Claude e ChatGPT)!

---

**Divirta-se!** 🎮⚔️

