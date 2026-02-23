-- ============================================================
-- storm_inserts.sql
-- Scenario: Storm "Aura" — February 2026
-- Severe storms and flooding across Portugal (Lisbon,
-- Setúbal, Tâmega/Douro, and Algarve regions).
-- Realistic community needs and volunteer offers.
-- NOTE: This script assumes the existing users (user_id 1–20)
--       and categories from model_inserts.sql are present.
--       It does NOT truncate existing data.
-- ============================================================

BEGIN;

-- ─── STORM NEEDS ─────────────────────────────────────────────────────────────
-- Approx. coordinates for affected areas:
--   Setúbal:            -8.8882, 38.5244
--   Montijo:            -8.9753, 38.7067
--   Barreiro:           -9.0721, 38.6600
--   Alcochete:          -8.9617, 38.7531
--   Portimão (Algarve): -8.5377, 37.1359
--   Faro (Algarve):     -7.9307, 37.0194
--   Amarante (Tâmega):  -8.0800, 41.2700
--   Marco de Canaveses: -8.1611, 41.1839
--   Odivelas (Lisbon):  -9.1853, 38.7948
--   Amadora (Lisbon):   -9.2268, 38.7533

INSERT INTO need (user_id, title, descrip, category, urgency, geom, address_point, status_id)
VALUES

-- ── CRITICAL ──────────────────────────────────────────────────────────────────

(3,  'Family stranded in Setúbal — urgent evacuation',
 'House surrounded by water after river overflow. Family with 2 children and an 82-year-old grandmother. Unable to leave. Need a boat or rescue team.',
 (SELECT category_id FROM category WHERE name_cat='safety'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8950, 38.5190), 4326), 3857),
 'Rua das Amendoeiras, Setúbal', 1),

(7,  'Elderly man alone — flooded home in Barreiro',
 '78-year-old man alone at home, water already at floor level. Reduced mobility, cannot climb stairs. Requires immediate evacuation.',
 (SELECT category_id FROM category WHERE name_cat='safety'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0740, 38.6580), 4326), 3857),
 'Rua Alfredo da Silva, Barreiro', 1),

(12, 'Insulin needed — access cut off by flooding',
 'Type 1 diabetic without insulin. Nearby pharmacy flooded, access road cut off. Urgent delivery needed via alternative route.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8870, 38.5280), 4326), 3857),
 'Bairro Viso, Setúbal', 1),

(5,  'Premature baby without heating — Portimão',
 '6-week-old baby at home without heating since early morning. Rain destroyed the roof. Family has nowhere to go. Critical situation.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.5390, 37.1340), 4326), 3857),
 'Urbanização Vale de Lagar, Portimão', 1),

(14, 'Isolated pregnant woman — Amarante',
 '38 weeks pregnant. Road flooded, husband abroad. No car and no neighbours. Urgently needs transport to hospital.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.0820, 41.2690), 4326), 3857),
 'Lugar de Bustelo, Amarante', 1),

(9,  'People trapped in flooded basement — Odivelas',
 'Two people trapped in a basement with water rising rapidly. Tried calling 112 but line is overloaded. Need immediate help.',
 (SELECT category_id FROM category WHERE name_cat='safety'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1870, 38.7930), 4326), 3857),
 'Rua Soeiro Pereira Gomes, Odivelas', 1),

(2,  'Dog trapped on rooftop — Marco de Canaveses',
 'Large dog trapped on the roof of a flooded house. Owner also stranded on the upper floor. Animal rescue and person rescue both needed.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.1630, 41.1820), 4326), 3857),
 'Lugar do Paço, Marco de Canaveses', 1),

(18, 'Child having seizures — no medical access',
 '4-year-old child with epilepsy history having seizures. Medication was left at school. Roads cut off, unable to reach hospital.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.9760, 38.7050), 4326), 3857),
 'Quinta do Marquês, Montijo', 1),

-- ── HIGH ──────────────────────────────────────────────────────────────────────

(1,  'Temporary shelter for family of 5 — Faro',
 'Family home uninhabitable after outer wall collapse. 3 minor children. Hotel refused entry due to missing documents. Need shelter tonight.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-7.9320, 37.0180), 4326), 3857),
 'Bairro de Figueiral, Faro', 1),

(6,  'Food and water for 8 people — Alcochete',
 'Building with 8 residents stranded for 24 hours. No food or drinking water. Children and elderly among those affected.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.9600, 38.7520), 4326), 3857),
 'Rua Marquês de Pombal, Alcochete', 1),

(10, 'Chronic medication missing — 3 days without',
 'Elderly woman with hypertension and diabetes without medication for 3 days. Local pharmacy closed. Family unable to reach it due to flooded roads.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0730, 38.6620), 4326), 3857),
 'Rua do Mercado, Barreiro', 1),

(15, 'Dry clothes and blankets — evacuated family',
 'Family of 4 evacuated at 3am. Left with only the clothes on their backs. No dry clothes, no warm layers. Sheltering at Setúbal sports hall.',
 (SELECT category_id FROM category WHERE name_cat='clothing'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8900, 38.5240), 4326), 3857),
 'Pavilhão Municipal de Setúbal', 1),

(19, 'Transport to evacuation centre — Amadora',
 'Family without a car needs transport to the evacuation centre. Street is flooded, walking is not possible. 2 young children.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.2290, 38.7510), 4326), 3857),
 'Rua Elias Garcia, Amadora', 1),

(4,  'Hygiene kits for evacuees — Portimão',
 'Group of 12 evacuees at the parish centre with no basic hygiene products. Need towels, soap, toothpaste and personal hygiene items.',
 (SELECT category_id FROM category WHERE name_cat='hygiene'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.5360, 37.1370), 4326), 3857),
 'Centro Paroquial de Portimão', 1),

(11, 'Emotional support — person in shock after flood',
 '55-year-old man lost all his possessions in the flood. In shock, alone and refusing to speak to strangers. Needs nearby psychological support.',
 (SELECT category_id FROM category WHERE name_cat='mental_health'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.0810, 41.2710), 4326), 3857),
 'Junta de Freguesia de Amarante', 1),

(16, 'Pet food for dog and cat — abandoned house',
 'Evacuated couple left two pets in an inaccessible home. Need someone who can reach the property and feed the animals.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0700, 38.6650), 4326), 3857),
 'Rua dos Pinheiros, Barreiro', 1),

(20, 'Urgent repair — partial roof collapse',
 'Partial roof collapse at a home after the storm. Elderly couple still inside. Needs urgent technical support to seal the opening.',
 (SELECT category_id FROM category WHERE name_cat='repairs'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8840, 38.5310), 4326), 3857),
 'Rua de São Sebastião, Setúbal', 1),

(8,  'Nappies and baby formula — Faro shelter',
 'Mother with a 3-month-old baby at the municipal shelter. No nappies, no formula. Nearby shop is closed.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-7.9310, 37.0200), 4326), 3857),
 'Abrigo Municipal, Faro', 1),

(13, 'Help filling in emergency housing forms',
 'Immigrant family does not speak Portuguese. Need help completing a housing support application at the local council. Urgent — deadline approaching.',
 (SELECT category_id FROM category WHERE name_cat='translation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.2280, 38.7540), 4326), 3857),
 'Câmara Municipal da Amadora', 1),

-- ── MEDIUM ────────────────────────────────────────────────────────────────────

(17, 'Help cleaning mud — house in Alcochete',
 'Flood left 20cm of mud throughout the house. Elderly owner has no strength to clean. Needs volunteers with brooms, buckets and gloves.',
 (SELECT category_id FROM category WHERE name_cat='other'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.9620, 38.7500), 4326), 3857),
 'Rua da Misericórdia, Alcochete', 1),

(3,  'Storage for belongings — house still flooded',
 'House still inaccessible. Family needs a place to store the few belongings they managed to save — boxes of clothes and documents.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8920, 38.5220), 4326), 3857),
 'Azeda, Setúbal', 1),

(6,  'Children need activities at the shelter',
 'About 15 children aged 3 to 10 are at the evacuation hall with nothing to do. Parents are exhausted. Need volunteers to keep the children occupied.',
 (SELECT category_id FROM category WHERE name_cat='childcare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.5370, 37.1350), 4326), 3857),
 'Pavilhão Desportivo, Portimão', 1),

(10, 'Legal advice — insurance refusing to pay',
 'Insurance company refusing to cover storm damage, citing force majeure. Family needs basic legal guidance on how to appeal.',
 (SELECT category_id FROM category WHERE name_cat='legal'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0710, 38.6640), 4326), 3857),
 'Barreiro', 1),

(14, 'Support for elderly woman after leaving shelter',
 '74-year-old woman returning home today. Needs someone to accompany her to assess the damage, make a list of needs and contact social services.',
 (SELECT category_id FROM category WHERE name_cat='eldercare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.1640, 41.1850), 4326), 3857),
 'Marco de Canaveses', 1),

(19, 'Blankets and bed linen — Amarante shelter',
 'Shelter received 30 more people this morning. Running short of blankets, pillows and bed linen. Council does not have enough stock.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.0790, 41.2720), 4326), 3857),
 'Escola Secundária de Amarante — Shelter', 1),

(1,  'Phone charging — no electricity for 2 days',
 'No electricity at home for 2 days. Phone nearly dead — the only way to contact children. Needs access to a power outlet or power bank.',
 (SELECT category_id FROM category WHERE name_cat='tech'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1860, 38.7960), 4326), 3857),
 'Odivelas', 1),

-- ── LOW ───────────────────────────────────────────────────────────────────────

(5,  'Donation collection — Setúbal reception centre',
 'Reception centre accepting donations of clothing, non-perishable food and hygiene products. Need volunteers to receive and organise items.',
 (SELECT category_id FROM category WHERE name_cat='donation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8870, 38.5250), 4326), 3857),
 'Centro de Acolhimento Municipal, Setúbal', 1),

(9,  'Documents lost in the flood — how to replace them',
 'Family lost national ID cards and birth certificates in the flood. Need guidance on how to replace documents and whether council support is available.',
 (SELECT category_id FROM category WHERE name_cat='legal'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.2250, 38.7530), 4326), 3857),
 'Amadora', 1),

(13, 'Missed classes — children at shelter',
 'Children at the emergency shelter missed school this week. Parents are asking for volunteers to do basic revision sessions in Portuguese and maths.',
 (SELECT category_id FROM category WHERE name_cat='education'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-7.9300, 37.0210), 4326), 3857),
 'Centro de Dia, Faro', 1);


-- ─── STORM OFFERS ─────────────────────────────────────────────────────────────

INSERT INTO offer (user_id, title, descrip, category, geom, address_point, status_id)
VALUES

(2,  '4x4 transport for flooded areas',
 'I have a Toyota Land Cruiser and can transport people and goods in flooded zones. Available today and tomorrow in Setúbal and surroundings.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8900, 38.5260), 4326), 3857),
 'Setúbal', 1),

(7,  'Temporary shelter — spare room available in Faro',
 'I have a free room at home. Can host a couple or a mother with child for up to 5 days. House has heating and food.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-7.9290, 37.0195), 4326), 3857),
 'Faro', 1),

(11, 'Volunteer nurse — on-site medical support',
 'I am a nurse with immediate availability. Can assist with basic triage, medication administration and health assessments at shelters.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.5380, 37.1360), 4326), 3857),
 'Portimão', 1),

(15, 'Clothes and blankets — immediate donation',
 'I have bags of winter clothing for adults and children, and 8 new blankets. Can deliver to a shelter in Setúbal or Barreiro.',
 (SELECT category_id FROM category WHERE name_cat='clothing'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0690, 38.6640), 4326), 3857),
 'Barreiro', 1),

(4,  'Psychologist available — free emotional support',
 'I am a clinical psychologist offering free emotional support sessions to flood victims. Available in person in Amarante or by phone.',
 (SELECT category_id FROM category WHERE name_cat='mental_health'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.0800, 41.2700), 4326), 3857),
 'Amarante', 1),

(18, 'Hot meals — improvised kitchen in Alcochete',
 'A group of neighbours is cooking hot meals to distribute. We can serve up to 30 meals per day. Looking for more ingredients and volunteers.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.9590, 38.7530), 4326), 3857),
 'Alcochete', 1),

(20, 'Tutor — academic support for evacuated children',
 'Primary school teacher available to provide academic support to children in emergency shelters. Available in the mornings in Marco de Canaveses.',
 (SELECT category_id FROM category WHERE name_cat='education'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.1620, 41.1840), 4326), 3857),
 'Marco de Canaveses', 1),

(3,  'Lawyer — free legal advice post-flood',
 'Civil law specialist offering free consultations to people affected by the floods who need support with insurance claims or housing issues.',
 (SELECT category_id FROM category WHERE name_cat='legal'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.2260, 38.7540), 4326), 3857),
 'Amadora', 1),

(6,  'Van available for donation transport',
 'I have a 9-seat van. Can run donation collection and delivery routes between Setúbal, Barreiro and Alcochete. Available on weekends.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.9750, 38.7070), 4326), 3857),
 'Montijo', 1),

(9,  'Cleanup volunteer — available as a team',
 'Organising a group of 6 volunteers with cleaning equipment (brooms, buckets, shovels). Can travel to any affected location in the Setúbal district.',
 (SELECT category_id FROM category WHERE name_cat='other'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-8.8880, 38.5250), 4326), 3857),
 'Setúbal', 1);


-- ─── STORM ASSIGNMENTS ────────────────────────────────────────────────────────
-- Needs are numbered sequentially after the existing inserts.
-- Assuming the last need_id from model_inserts.sql was 31
-- and the last offer_id was 25, storm records start from:
--   need_id: 32 onwards
--   offer_id: 26 onwards

-- Accepted/proposed matches — mostly unresolved to reflect ongoing emergency

INSERT INTO assignments (need_id, offer_id, status_ass, notes)
VALUES
-- Isolated pregnant woman → 4x4 transport
(36, 26, 'accepted',  'Driver confirmed departure. Alternative route via EN101 identified.'),
-- Family of 5 without shelter → Room in Faro
(40, 27, 'accepted',  'Family accommodated. Room available for 5 days.'),
-- Premature baby without heating → Volunteer nurse
(35, 28, 'proposed',  'Nurse available but awaiting confirmation of street access.'),
-- Dry clothes for evacuated family → Clothes and blankets
(46, 29, 'accepted',  'Delivery made to Setúbal municipal sports hall.'),
-- Emotional support for man in shock → Psychologist
(47, 30, 'proposed',  'Psychologist travelled to the location, waiting for the person to accept contact.'),
-- Food and water for 8 people → Improvised kitchen
(41, 31, 'accepted',  'Meals delivered. Group will repeat tomorrow morning.'),
-- Children with no activities → Tutor
(53, 32, 'proposed',  'Teacher confirmed attendance tomorrow at 9am at the Portimão sports hall.'),
-- Legal advice on insurance → Free lawyer
(50, 33, 'accepted',  'Consultation scheduled for Monday at 2pm.'),
-- Donation collection → Transport van
(58, 34, 'accepted',  'Route set: Setúbal → Barreiro → Alcochete on Saturday.'),
-- Help cleaning mud → Cleanup volunteers
(48, 35, 'proposed',  'Cleanup team available but waiting for water levels to drop.');

COMMIT;
