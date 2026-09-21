# Content audit

Dataset **2.0.0** · D&D 5e (2014), official errata; revised Bladesinger explicitly scoped in Q094

Generated from `questions/`, `answers/`, and `dataset.json`; edit those files, then run `python manage_dataset.py`.

Reviewed on **2026-09-21** against baseline commit `3ce375f`. All 100 items were inspected.

- Source-verified: **93**
- Explicitly interpretive: **1**
- Provisional, pending primary-source access: **6**

These statuses describe the content audit, not model performance. Automated tests check data consistency and known regressions; they cannot prove a D&D ruling true. The audit is a source-backed editorial review, not an independent expert certification.

## Changes and remaining work

69 items have a changed question and/or answer; 31 retain both original texts. Reworded or replaced questions make version 2 scores incomparable with the old dataset. Originals remain available in Git at the baseline commit.

The original multiple-choice bank contained wrong keys, a numeric key instead of a letter, questions with multiple correct choices, and stems with no correct choice. Scenario answers invented rules for feats, spell components, control limits, and armor. Ambiguous premises were narrowed; Q010, Q034, and Q073 were substantially reframed.

The following full-text sources could not be accessed in this audit. Provisional corrections are recorded but excluded from automatic scoring. A reviewer with the listed 2014 books must check the question, answer, and conditions before changing its status to verified:

- **Q058** — Backgrounds: Guild Artisan (p. 132). One artisan-tool proficiency. Primary full text not accessible in this audit; retained provisionally.
- **Q067** — Feats: Mobile (p. 168). Corrected feat name and separated its +10-foot speed benefit from its Dash/difficult-terrain benefit. Full text needs verification.
- **Q068** — Between Adventures: Crafting a Magic Item (pp. 128-129). 100 gp divided by 25 gp/day is four days; old 100-day answer was wrong. Arithmetic is clear, but the 2014 option's source needs verification.
- **Q069** — Fighter: Eldritch Knight Spellcasting table (p. 75). Provisional correction to third-level maximum at fighter 14; fourth-level slots arrive at 19. No new slot level is gained at 14.
- **Q081** — Feats: Mounted Combatant (p. 168). Provisional replacement of fabricated rider defenses with melee advantage against smaller unmounted targets; full feat needs source verification.
- **Q096** — Treasure: Variant, Mixing Potions (p. 140). Optional, not compulsory. Removed unsupported outcome ranges; full primary table remains unverified and item is excluded from scoring.

Q088 is intentionally an interpretation question: reward the explicit restrictions and recognition of the portal issue, not one forced teleportation ruling. Q079 excludes the disputed damage-modifier question from its rubric.

## Method and sources

Use the 2014 rules, applying official errata where they update the older SRD text. In particular, the Player's Handbook errata makes a simulacrum a construct; the SCAG errata supplies Q094's revised cantrip substitution. Book/page locators for inaccessible material are follow-up references, not proof it was read. Forum posts and current-edition replacements are not primary-source verification.

- [System Reference Document 5.1 (2014 rules, CC BY 4.0)](https://www.dndbeyond.com/attachments/39j2li89/SRD5.1-CCBY4.0License.pdf) — public.
- [Basic Rules (2014), Magic Items](https://www.dndbeyond.com/sources/dnd/basic-rules-2014/magic-items) — public.
- [D&D Beyond feat index, explicitly marked Player's Handbook (2014) entries](https://www.dndbeyond.com/feats) — public_summary.
- [Player's Handbook (2014)](https://www.dndbeyond.com/sources/dnd/phb-2014) — purchase_required.
- [Dungeon Master's Guide (2014)](https://www.dndbeyond.com/sources/dnd/dmg-2014) — purchase_required.
- [Sage Advice Compendium (2014), official rulings](https://www.dndbeyond.com/sources/dnd/sac/sage-advice-compendium) — public.
- [Sword Coast Adventurer's Guide errata v2.2 (2021)](https://media.wizards.com/2021/dnd/downloads/SCAG-Errata.pdf) — public.
- [Player's Handbook errata v2.0.2 (2020; hosted at a 2018 URL)](https://media.wizards.com/2018/dnd/downloads/PH-Errata.pdf) — public.
- [Basic Rules (2014), Personality and Background](https://www.dndbeyond.com/sources/dnd/basic-rules-2014/personality-and-background) — public.

## Item-by-item ledger

| Item | Status | Changed | Finding and rule locator |
|---|---|---|---|
| [Q001](../questions/Q001.md) / [answer](../answers/Q001.md) | verified | retained | 18 gives +4. **Source:** srd; Using Ability Scores: Ability Scores and Modifiers. |
| [Q002](../questions/Q002.md) / [answer](../answers/Q002.md) | verified | retained | Versatile is the listed property. **Source:** srd; Equipment: Weapons table, longsword. |
| [Q003](../questions/Q003.md) / [answer](../answers/Q003.md) | verified | question | Clarified 2014 action economy; healing potions use an action. **Source:** srd, basic_items; Magic Items: Activating an Item; Combat: Two-Weapon Fighting; Rage; Misty Step. |
| [Q004](../questions/Q004.md) / [answer](../answers/Q004.md) | verified | question | Ends at the end of the monk's next turn, not a fixed duration measured from the hit. **Source:** srd; Monk: Stunning Strike (p. 28). |
| [Q005](../questions/Q005.md) / [answer](../answers/Q005.md) | verified | retained | Automatic Strength and Dexterity saving-throw failures. **Source:** srd; Conditions: Unconscious. |
| [Q006](../questions/Q006.md) / [answer](../answers/Q006.md) | verified | question | Three simultaneous items, not a daily limit. **Source:** srd; Magic Items: Attunement. |
| [Q007](../questions/Q007.md) / [answer](../answers/Q007.md) | verified | answer | Three darts plus one per slot level above first gives five, not six. **Source:** srd; Magic Missile (p. 161). |
| [Q008](../questions/Q008.md) / [answer](../answers/Q008.md) | verified | retained | Half cover grants +2 AC and Dexterity saves. **Source:** srd; Combat: Cover. |
| [Q009](../questions/Q009.md) / [answer](../answers/Q009.md) | verified | question_and_answer | AC 17; distinguished monster, magic item, and animated-object spell statistics. **Source:** srd; Animated Objects: Flying Sword (p. 264). |
| [Q010](../questions/Q010.md) / [answer](../answers/Q010.md) | verified | question_and_answer | Replaced a multiple-correct-answer stem with the fighter's unique four-attack progression. **Source:** srd; Fighter: Extra Attack. |
| [Q011](../questions/Q011.md) / [answer](../answers/Q011.md) | verified | retained | A third-level casting automatically counters spells of third level or lower, assuming a legal target. **Source:** srd; Counterspell. |
| [Q012](../questions/Q012.md) / [answer](../answers/Q012.md) | verified | question | Included all squeezing penalties, not an incomplete speed-halving shorthand. **Source:** srd; Combat: Squeezing into a Smaller Space (p. 92). |
| [Q013](../questions/Q013.md) / [answer](../answers/Q013.md) | verified | answer | Comfortable costs 2 gp/day, not 1 gp/day. **Source:** srd; Equipment: Lifestyle Expenses table (p. 73). |
| [Q014](../questions/Q014.md) / [answer](../answers/Q014.md) | verified | retained | Default darkvision is 60 feet. **Source:** srd; Races: Tiefling (p. 7). |
| [Q015](../questions/Q015.md) / [answer](../answers/Q015.md) | verified | question | Base Rage resists all bludgeoning, piercing, and slashing, but not fire; excluded subclass exceptions. **Source:** srd; Barbarian: Rage (p. 8). |
| [Q016](../questions/Q016.md) / [answer](../answers/Q016.md) | verified | question | Old question also had V and S as correct answers. All new choices are material components; the priced diamond is required. **Source:** srd, sac; Spellcasting: Material Components; SAC: Components. |
| [Q017](../questions/Q017.md) / [answer](../answers/Q017.md) | verified | question | A short rest lasts at least one hour. **Source:** srd; Resting: Short Rest (p. 87). |
| [Q018](../questions/Q018.md) / [answer](../answers/Q018.md) | verified | question | Specified eligible rolls and the 2014 advantage mechanic. **Source:** basic_personality; Personality and Background: Inspiration, Using Inspiration. |
| [Q019](../questions/Q019.md) / [answer](../answers/Q019.md) | verified | retained | Rapier damage is 1d8. **Source:** srd; Equipment: Weapons table. |
| [Q020](../questions/Q020.md) / [answer](../answers/Q020.md) | verified | retained | Official legacy summary confirms medium armor and shields; do not use the revised 2024 feat. **Source:** feats; Moderately Armored, Player's Handbook (2014) entry. |
| [Q021](../questions/Q021.md) / [answer](../answers/Q021.md) | verified | retained | Damage calls for a Constitution saving throw, not an ability check. **Source:** srd; Spellcasting: Concentration. |
| [Q022](../questions/Q022.md) / [answer](../answers/Q022.md) | verified | question | 10 plus the full Perception modifier; excluded advantage and other modifiers. **Source:** srd; Using Ability Scores: Passive Checks. |
| [Q023](../questions/Q023.md) / [answer](../answers/Q023.md) | verified | retained | A roll of 10 or higher succeeds. **Source:** srd; Combat: Death Saving Throws. |
| [Q024](../questions/Q024.md) / [answer](../answers/Q024.md) | verified | retained | A level-3 sorcerer knows four cantrips. **Source:** srd; Sorcerer table (p. 42). |
| [Q025](../questions/Q025.md) / [answer](../answers/Q025.md) | verified | question | Specified wizard class levels to avoid fighter, rogue, and multiclass exceptions. **Source:** srd; Wizard: Ability Score Improvement. |
| [Q026](../questions/Q026.md) / [answer](../answers/Q026.md) | verified | retained | The area is a 20-foot cube. **Source:** srd; Faerie Fire. |
| [Q027](../questions/Q027.md) / [answer](../answers/Q027.md) | verified | question_and_answer | Plate 18 plus shield 2 equals 20, not 18. **Source:** srd; Equipment: Armor table. |
| [Q028](../questions/Q028.md) / [answer](../answers/Q028.md) | verified | question | Specified running start and movement budget; distance is Strength score in feet. **Source:** srd; Adventuring: Jumping. |
| [Q029](../questions/Q029.md) / [answer](../answers/Q029.md) | verified | question | Poison immunity prevents poison damage absent an explicit exception. **Source:** srd; Monsters: Vulnerabilities, Resistances, and Immunities. |
| [Q030](../questions/Q030.md) / [answer](../answers/Q030.md) | verified | retained | +5 AC for the spell's duration, including the triggering attack. **Source:** srd; Shield. |
| [Q031](../questions/Q031.md) / [answer](../answers/Q031.md) | verified | question | Double the attack's damage dice, not modifiers or the entire rolled total. **Source:** srd; Combat: Critical Hits. |
| [Q032](../questions/Q032.md) / [answer](../answers/Q032.md) | verified | question | Loading applies per firing action, bonus action, or reaction, not once per whole turn. **Source:** srd; Equipment: Ammunition and Loading. |
| [Q033](../questions/Q033.md) / [answer](../answers/Q033.md) | verified | retained | Pact Magic slots are fifth level; Mystic Arcanum is a separate feature. **Source:** srd; Warlock table (p. 46). |
| [Q034](../questions/Q034.md) / [answer](../answers/Q034.md) | verified | question_and_answer | Replaced an undefined corridor/splash-grid question with the total-cover rule. **Source:** srd; Spellcasting: Areas of Effect (pp. 102-103). |
| [Q035](../questions/Q035.md) / [answer](../answers/Q035.md) | verified | retained | Initiative count 20, losing ties. **Source:** srd; Legendary Creatures: Lair Actions (p. 260). |
| [Q036](../questions/Q036.md) / [answer](../answers/Q036.md) | verified | question | Releasing the readied shot uses a reaction when the trigger finishes. **Source:** srd; Combat: Ready. |
| [Q037](../questions/Q037.md) / [answer](../answers/Q037.md) | verified | retained | Dexterity and Intelligence. **Source:** srd; Rogue: Proficiencies. |
| [Q038](../questions/Q038.md) / [answer](../answers/Q038.md) | verified | retained | Bonus applies to attack and damage rolls. **Source:** srd; Magic Items: Weapon, +1, +2, or +3. |
| [Q039](../questions/Q039.md) / [answer](../answers/Q039.md) | verified | question | Spell creates up to ten, not necessarily exactly ten; question now asks the maximum. **Source:** srd; Goodberry. |
| [Q040](../questions/Q040.md) / [answer](../answers/Q040.md) | verified | answer | Ten minutes of concentration makes the wall permanent, not one minute. **Source:** srd; Wall of Stone (pp. 190-191). |
| [Q041](../questions/Q041.md) / [answer](../answers/Q041.md) | verified | question | Specified sight and 30-foot range; ranged attacks within 5 feet are not inherently disadvantaged by prone. **Source:** srd; Faerie Fire; Conditions: Prone; Advantage and Disadvantage. |
| [Q042](../questions/Q042.md) / [answer](../answers/Q042.md) | verified | question_and_answer | Normal casting takes one minute; a ritual would take eleven minutes. **Source:** srd; Identify (p. 155); Spellcasting: Rituals. |
| [Q043](../questions/Q043.md) / [answer](../answers/Q043.md) | verified | retained | Maximum falling damage is 20d6. **Source:** srd; Adventuring: Falling. |
| [Q044](../questions/Q044.md) / [answer](../answers/Q044.md) | verified | question | Restrained sets speed to zero; it does not halve speed. **Source:** srd; Conditions: Restrained. |
| [Q045](../questions/Q045.md) / [answer](../answers/Q045.md) | verified | answer | Flight becomes available at druid level 8; key must contain option D, not numeral 8. **Source:** srd; Druid: Wild Shape, Beast Shapes. |
| [Q046](../questions/Q046.md) / [answer](../answers/Q046.md) | verified | answer | Alchemist's supplies cost 50 gp, not 30 gp. **Source:** srd; Equipment: Tools table (p. 70). |
| [Q047](../questions/Q047.md) / [answer](../answers/Q047.md) | verified | retained | Walking speed is 25 feet and heavy armor does not reduce it. **Source:** srd; Races: Dwarf (p. 3). |
| [Q048](../questions/Q048.md) / [answer](../answers/Q048.md) | verified | question | No actions or reactions. **Source:** srd; Conditions: Incapacitated. |
| [Q049](../questions/Q049.md) / [answer](../answers/Q049.md) | verified | question | Restriction applies only to the same turn and allows one-action cantrips. **Source:** srd; Spellcasting: Bonus Action (p. 101). |
| [Q050](../questions/Q050.md) / [answer](../answers/Q050.md) | verified | question | 10 plus Dexterity and Constitution modifiers; shield remains allowed. **Source:** srd; Barbarian: Unarmored Defense (p. 8). |
| [Q051](../questions/Q051.md) / [answer](../answers/Q051.md) | verified | retained | Hit Die is d8 per cleric level. **Source:** srd; Cleric: Hit Points. |
| [Q052](../questions/Q052.md) / [answer](../answers/Q052.md) | verified | question_and_answer | Strength 13 AND Charisma 13, not either score. **Source:** srd; Multiclassing Prerequisites table. |
| [Q053](../questions/Q053.md) / [answer](../answers/Q053.md) | verified | question | Greatsword deals 2d6; changed singular die to dice. **Source:** srd; Equipment: Weapons table. |
| [Q054](../questions/Q054.md) / [answer](../answers/Q054.md) | verified | retained | Range is 150 feet, distinct from area radius. **Source:** srd; Fireball. |
| [Q055](../questions/Q055.md) / [answer](../answers/Q055.md) | verified | question_and_answer | 6500 total XP; moving from the level-4 minimum of 2700 requires 3800 more. Removed total/increment ambiguity. **Source:** srd; Beyond 1st Level: Character Advancement table. |
| [Q056](../questions/Q056.md) / [answer](../answers/Q056.md) | verified | retained | Can spend any or all remaining Hit Dice. **Source:** srd; Resting: Short Rest. |
| [Q057](../questions/Q057.md) / [answer](../answers/Q057.md) | verified | retained | V is verbal. **Source:** srd; Spellcasting: Components. |
| [Q058](../questions/Q058.md) / [answer](../answers/Q058.md) | provisional | retained | One artisan-tool proficiency. Primary full text not accessible in this audit; retained provisionally. **Source:** phb; Backgrounds: Guild Artisan (p. 132). |
| [Q059](../questions/Q059.md) / [answer](../answers/Q059.md) | verified | retained | At level 10 the die becomes d10. **Source:** srd; Bard: Bardic Inspiration (p. 12). |
| [Q060](../questions/Q060.md) / [answer](../answers/Q060.md) | verified | question_and_answer | A small taste identifies the potion; removed invented DC 15 Arcana rule. **Source:** basic_items; Using a Magic Item. |
| [Q061](../questions/Q061.md) / [answer](../answers/Q061.md) | verified | retained | Healer's kit weighs 3 lb. **Source:** srd; Equipment: Adventuring Gear table (p. 69). |
| [Q062](../questions/Q062.md) / [answer](../answers/Q062.md) | verified | retained | Abjuration. **Source:** srd; Shield. |
| [Q063](../questions/Q063.md) / [answer](../answers/Q063.md) | verified | question | 50 gp per spell level; distinguished copying a new spell from replacing one's own book and excluded discounts. **Source:** srd; Wizard: Your Spellbook, Copying a Spell into the Book. |
| [Q064](../questions/Q064.md) / [answer](../answers/Q064.md) | verified | retained | Highest individual CR is 2; upcasting increases numbers, not the maximum CR. **Source:** srd; Conjure Woodland Beings (p. 129). |
| [Q065](../questions/Q065.md) / [answer](../answers/Q065.md) | verified | question | Listed average is 17 HP (5d6); clarified monster rather than Animate Objects. **Source:** srd; Animated Objects: Flying Sword (p. 264). |
| [Q066](../questions/Q066.md) / [answer](../answers/Q066.md) | verified | retained | Wisdom saving throw. **Source:** srd; Hold Person. |
| [Q067](../questions/Q067.md) / [answer](../answers/Q067.md) | provisional | question_and_answer | Corrected feat name and separated its +10-foot speed benefit from its Dash/difficult-terrain benefit. Full text needs verification. **Source:** phb; Feats: Mobile (p. 168). |
| [Q068](../questions/Q068.md) / [answer](../answers/Q068.md) | provisional | question_and_answer | 100 gp divided by 25 gp/day is four days; old 100-day answer was wrong. Arithmetic is clear, but the 2014 option's source needs verification. **Source:** dmg; Between Adventures: Crafting a Magic Item (pp. 128-129). |
| [Q069](../questions/Q069.md) / [answer](../answers/Q069.md) | provisional | question_and_answer | Provisional correction to third-level maximum at fighter 14; fourth-level slots arrive at 19. No new slot level is gained at 14. **Source:** phb; Fighter: Eldritch Knight Spellcasting table (p. 75). |
| [Q070](../questions/Q070.md) / [answer](../answers/Q070.md) | verified | question | One attunement if required; artifact rarity alone does not establish an attunement requirement. **Source:** srd; Magic Items: Attunement. |
| [Q071](../questions/Q071.md) / [answer](../answers/Q071.md) | verified | question | Glaive adds five feet to normal reach for its attacks; specified normal reach of five feet. **Source:** srd; Equipment: Reach and Weapons table. |
| [Q072](../questions/Q072.md) / [answer](../answers/Q072.md) | verified | retained | Adds d4 to one ability check under the spell's conditions. **Source:** srd; Guidance. |
| [Q073](../questions/Q073.md) / [answer](../answers/Q073.md) | verified | question_and_answer | Replaced an undefined underwater long-jump trick question with explicit swimming movement cost. **Source:** srd; Adventuring: Climbing, Swimming, and Crawling. |
| [Q074](../questions/Q074.md) / [answer](../answers/Q074.md) | verified | answer | 1d10 plus fighter level, not Constitution modifier. **Source:** srd; Fighter: Second Wind. |
| [Q075](../questions/Q075.md) / [answer](../answers/Q075.md) | verified | retained | Six levels cause death in the 2014 rules. **Source:** srd; Conditions: Exhaustion. |
| [Q076](../questions/Q076.md) / [answer](../answers/Q076.md) | verified | question_and_answer | Material component remains; specified visible handling. Removed imaginary identification/Ready rules. **Source:** srd, sac; Subtle Spell; Hold Monster; Counterspell; SAC: Sorcerer. |
| [Q077](../questions/Q077.md) / [answer](../answers/Q077.md) | verified | question_and_answer | Already resolved attack remains; no movement/actions through next turn and no additional speed halving. **Source:** srd; Haste (p. 153); Combat: Bonus Actions. |
| [Q078](../questions/Q078.md) / [answer](../answers/Q078.md) | verified | question_and_answer | DC 14, modifier +3 under explicit assumptions; damaged caster and transformed ally are different creatures. **Source:** srd; Spellcasting: Concentration; Polymorph. |
| [Q079](../questions/Q079.md) / [answer](../answers/Q079.md) | verified | question_and_answer | 20-foot item-specific throw, no immediate fire tick, no alchemist-tool attack proficiency, DC 10 Dexterity extinguishing check. Damage-modifier debate excluded. **Source:** srd; Equipment: Alchemist's Fire (p. 66), Improvised Weapons, Tools. |
| [Q080](../questions/Q080.md) / [answer](../answers/Q080.md) | verified | question_and_answer | Added the missing extra-action requirement; once per turn does not mean once per round. **Source:** srd; Rogue: Sneak Attack; Fighter: Action Surge; Combat: Ready. |
| [Q081](../questions/Q081.md) / [answer](../answers/Q081.md) | provisional | question_and_answer | Provisional replacement of fabricated rider defenses with melee advantage against smaller unmounted targets; full feat needs source verification. **Source:** phb; Feats: Mounted Combatant (p. 168). |
| [Q082](../questions/Q082.md) / [answer](../answers/Q082.md) | verified | question_and_answer | Specified warlock invocation and enemy senses to avoid assuming everyone inside is blinded. **Source:** srd; Warlock: Devil's Sight; Darkness; Combat: Unseen Attackers and Targets. |
| [Q083](../questions/Q083.md) / [answer](../answers/Q083.md) | verified | question_and_answer | Removed fabricated no-healing clause; distinguish laboratory repair, Wish's listed restoration, construct healing exclusions, and wish stress. **Source:** srd, phb_errata; Simulacrum (p. 180); Wish (p. 193); Cure Wounds; PH errata: Simulacrum. |
| [Q084](../questions/Q084.md) / [answer](../answers/Q084.md) | verified | question_and_answer | Dragging exception requires target at least two sizes smaller, not one. **Source:** srd; Combat: Grappling, Moving a Grappled Creature; Conditions: Prone. |
| [Q085](../questions/Q085.md) / [answer](../answers/Q085.md) | verified | question_and_answer | Magic expires at 24 hours; bag has no time-stasis rule and spell does not say berries wither. **Source:** srd; Goodberry; Bag of Holding. |
| [Q086](../questions/Q086.md) / [answer](../answers/Q086.md) | verified | question_and_answer | Immediate reversion, carryover damage, and later healing in normal form; 0 beast HP does not necessarily mean unconscious druid. **Source:** srd; Druid: Wild Shape. |
| [Q087](../questions/Q087.md) / [answer](../answers/Q087.md) | verified | question_and_answer | Official ruling confirms Mobile can prevent the opportunity attack; removed fictional Mobile effects. **Source:** sac; Feats: Sentinel, interaction with Mobile. |
| [Q088](../questions/Q088.md) / [answer](../answers/Q088.md) | interpretation | question_and_answer | Boundary restriction works both ways; caster leaving ends hut. Teleport/portal interpretation is explicitly not a fixed yes/no answer. **Source:** srd; Tiny Hut (p. 187); Teleportation Circle (p. 186). |
| [Q089](../questions/Q089.md) / [answer](../answers/Q089.md) | verified | answer | Specific restoration restriction after disintegration; being hit without disintegrating is a different situation. **Source:** srd, phb_errata; Disintegrate; Revivify; PH errata: Disintegrate. |
| [Q090](../questions/Q090.md) / [answer](../answers/Q090.md) | verified | answer | Interruptions resolve inside-out; each needs its own eligible reaction and slot. **Source:** srd, sac; Counterspell; Combat: Reactions; SAC: Casting Time. |
| [Q091](../questions/Q091.md) / [answer](../answers/Q091.md) | verified | question_and_answer | One created or four renewed at third level, plus two per higher slot level; separate castings are additive across groups, control lasts 24 hours. **Source:** srd; Animate Dead (pp. 115-116). |
| [Q092](../questions/Q092.md) / [answer](../answers/Q092.md) | verified | question_and_answer | At least one hour is sufficient; first hour-long fight already interrupts. Removed incorrect XGE attribution. **Source:** srd; Resting: Long Rest (p. 87). |
| [Q093](../questions/Q093.md) / [answer](../answers/Q093.md) | verified | question_and_answer | Cannot hide from clear sight; DM judges circumstances; no blanket cover prerequisite or automatic hidden status from invisibility. **Source:** srd; Using Ability Scores: Hiding; Conditions: Invisible. |
| [Q094](../questions/Q094.md) / [answer](../answers/Q094.md) | verified | question_and_answer | Version locked to revised feature; example includes a free hand for somatic casting. **Source:** scag_errata, srd; SCAG errata p. 1: Extra Attack; Shocking Grasp. |
| [Q095](../questions/Q095.md) / [answer](../answers/Q095.md) | verified | question_and_answer | Specified stat block, whose resistance excludes silvered attacks; silver does not make weapon magical. **Source:** srd; Devils: Barbed Devil; Equipment: Silvered Weapons. |
| [Q096](../questions/Q096.md) / [answer](../answers/Q096.md) | provisional | question_and_answer | Optional, not compulsory. Removed unsupported outcome ranges; full primary table remains unverified and item is excluded from scoring. **Source:** dmg; Treasure: Variant, Mixing Potions (p. 140). |
| [Q097](../questions/Q097.md) / [answer](../answers/Q097.md) | verified | question_and_answer | No armor-specific Athletics disadvantage; separated nonproficiency, Strength, encumbrance, and rough-water checks. **Source:** srd; Equipment: Armor; Adventuring: Swimming. |
| [Q098](../questions/Q098.md) / [answer](../answers/Q098.md) | verified | question_and_answer | Dropping costs no action or speed on your turn; no saving-throw advantage; standing costs half speed. **Source:** srd; Combat: Being Prone; Conditions: Prone; Lightning Bolt. |
| [Q099](../questions/Q099.md) / [answer](../answers/Q099.md) | verified | question_and_answer | Crit protection irrelevant; repeated damage needs bonus action; disadvantage lasts until caster's next turn and can be reapplied. **Source:** srd; Heat Metal (p. 153); Adamantine Armor (p. 207). |
| [Q100](../questions/Q100.md) / [answer](../answers/Q100.md) | verified | question_and_answer | Legendary Resistance changes failure to success; destruction requires the cleric feature and eligible CR. **Source:** srd; Cleric: Turn Undead and Destroy Undead; Legendary Resistance trait. |
