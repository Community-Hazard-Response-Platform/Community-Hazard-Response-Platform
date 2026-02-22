BEGIN;

TRUNCATE TABLE assignments RESTART IDENTITY CASCADE;
TRUNCATE TABLE offer RESTART IDENTITY CASCADE;
TRUNCATE TABLE need RESTART IDENTITY CASCADE;
TRUNCATE TABLE category RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_user RESTART IDENTITY CASCADE;

-- ─── USERS ────────────────────────────────────────────────────────────────────

INSERT INTO app_user (username, email, hashed_password, firstname, surname, phone, is_verified) VALUES
('user01','user01@example.com','$2b$12$dummyhash01','Alex','Silva',     '+351910000001', TRUE),
('user02','user02@example.com','$2b$12$dummyhash02','Bea','Costa',      '+351910000002', TRUE),
('user03','user03@example.com','$2b$12$dummyhash03','Carla','Ramos',    '+351910000003', TRUE),
('user04','user04@example.com','$2b$12$dummyhash04','Diogo','Pereira',  '+351910000004', TRUE),
('user05','user05@example.com','$2b$12$dummyhash05','Eva','Almeida',    '+351910000005', TRUE),
('user06','user06@example.com','$2b$12$dummyhash06','Filipe','Rocha',   '+351910000006', TRUE),
('user07','user07@example.com','$2b$12$dummyhash07','Gabi','Santos',    '+351910000007', TRUE),
('user08','user08@example.com','$2b$12$dummyhash08','Hugo','Ferreira',  '+351910000008', TRUE),
('user09','user09@example.com','$2b$12$dummyhash09','Ines','Carvalho',  '+351910000009', TRUE),
('user10','user10@example.com','$2b$12$dummyhash10','Joao','Martins',   '+351910000010', TRUE),
('user11','user11@example.com','$2b$12$dummyhash11','Katia','Lopes',    '+351910000011', TRUE),
('user12','user12@example.com','$2b$12$dummyhash12','Luis','Gomes',     '+351910000012', TRUE),
('user13','user13@example.com','$2b$12$dummyhash13','Marta','Sousa',    '+351910000013', TRUE),
('user14','user14@example.com','$2b$12$dummyhash14','Nuno','Neves',     '+351910000014', TRUE),
('user15','user15@example.com','$2b$12$dummyhash15','Olga','Correia',   '+351910000015', TRUE),
('user16','user16@example.com','$2b$12$dummyhash16','Paulo','Teixeira', '+351910000016', TRUE),
('user17','user17@example.com','$2b$12$dummyhash17','Rita','Nogueira',  '+351910000017', TRUE),
('user18','user18@example.com','$2b$12$dummyhash18','Sara','Araujo',    '+351910000018', TRUE),
('user19','user19@example.com','$2b$12$dummyhash19','Tiago','Mendes',   '+351910000019', TRUE),
('user20','user20@example.com','$2b$12$dummyhash20','Vasco','Pinto',    '+351910000020', TRUE);

-- ─── CATEGORIES ───────────────────────────────────────────────────────────────

INSERT INTO category (name_cat, descrip) VALUES
('food',         'Groceries, meals, water, baby formula'),
('medical',      'Medication pickup, escort to doctor, basic care'),
('transport',    'Rides to appointments, delivery runs'),
('social',       'Companionship, check-ins, administrative support'),
('shelter',      'Temporary accommodation, blankets, essentials'),
('pets',         'Pet food, vet transport, temporary fostering'),
('clothing',     'Warm clothes, coats, shoes'),
('hygiene',      'Hygiene kits, diapers, cleaning supplies'),
('childcare',    'Short childcare support for emergencies'),
('eldercare',    'Support for elderly: visits, errands'),
('repairs',      'Small home repairs, urgent fixes'),
('translation',  'Translation/interpretation help'),
('legal',        'Basic legal guidance signposting'),
('education',    'Tutoring, homework support'),
('tech',         'Help with phones, online forms, setup'),
('mental_health','Listening support and signposting to services'),
('donation',     'Donation pickup/drop-off coordination'),
('logistics',    'Storage, packing, moving essentials'),
('safety',       'Safety planning, escorting, awareness'),
('other',        'Miscellaneous needs');

-- ─── NEEDS (Lisbon, all categories and urgency levels) ────────────────────────

INSERT INTO need (user_id, title, descrip, category, urgency, geom, address_point, status_id)
VALUES
-- CRITICAL
(1,  'Need medication today',           'Out of medication, urgent pickup needed.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1393, 38.7139), 4326), 3857), 'Baixa, Lisboa', 1),

(2,  'Emergency shelter needed',        'Evicted today, need somewhere to sleep tonight.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1359, 38.7117), 4326), 3857), 'Alfama, Lisboa', 1),

(3,  'Baby formula urgently needed',    'Ran out of baby formula, no money until Friday.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1370, 38.7250), 4326), 3857), 'Penha de Franca, Lisboa', 1),

(4,  'Childcare emergency',             'Need someone to watch my child for 2 hours urgently.',
 (SELECT category_id FROM category WHERE name_cat='childcare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1280, 38.7300), 4326), 3857), 'Mouraria, Lisboa', 1),

(5,  'Need a ride to dialysis',         'Weekly dialysis appointment, no transport available.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1600, 38.7300), 4326), 3857), 'Benfica, Lisboa', 1),

(6,  'Urgent food needed',              'Single mother with no food at home.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1520, 38.7100), 4326), 3857), 'Alcantara, Lisboa', 1),

(7,  'Emergency shelter Parque Nacoes', 'Need temporary accommodation for one night.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.0943, 38.7633), 4326), 3857), 'Parque das Nacoes, Lisboa', 1),

(8,  'Medical emergency supplies',      'Diabetic person needs insulin, ran out this morning.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1410, 38.7160), 4326), 3857), 'Rossio, Lisboa', 1),

-- HIGH
(9,  'Grocery delivery needed',         'Need groceries delivered, elderly person alone at home.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1490, 38.7080), 4326), 3857), 'Estrela, Lisboa', 1),

(10, 'Need warm clothes',               'Homeless person needs winter clothing urgently.',
 (SELECT category_id FROM category WHERE name_cat='clothing'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1320, 38.7200), 4326), 3857), 'Intendente, Lisboa', 1),

(11, 'Mental health support',           'Looking for someone to talk to, feeling very isolated.',
 (SELECT category_id FROM category WHERE name_cat='mental_health'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1600, 38.7150), 4326), 3857), 'Amoreiras, Lisboa', 1),

(12, 'Safety escort needed',            'Woman needs escort home late at night.',
 (SELECT category_id FROM category WHERE name_cat='safety'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1480, 38.7200), 4326), 3857), 'Intendente, Lisboa', 1),

(13, 'Diapers needed',                  'Young family ran out of diapers.',
 (SELECT category_id FROM category WHERE name_cat='hygiene'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1290, 38.7180), 4326), 3857), 'Olivais, Lisboa', 1),

(14, 'Help moving essentials',          'Need help moving a few boxes after eviction.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1410, 38.7280), 4326), 3857), 'Chelas, Lisboa', 1),

(15, 'Elderly check-in needed',         'Neighbour not answering door, need welfare check.',
 (SELECT category_id FROM category WHERE name_cat='eldercare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1330, 38.7120), 4326), 3857), 'Marvila, Lisboa', 1),

(16, 'Home repair urgent',              'Broken window needs fixing before rain.',
 (SELECT category_id FROM category WHERE name_cat='repairs'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1480, 38.7120), 4326), 3857), 'Prazeres, Lisboa', 1),

(17, 'Wheelchair transport',            'Need accessible transport to hospital appointment.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1550, 38.7050), 4326), 3857), 'Ajuda, Lisboa', 1),

(18, 'Pet food needed urgently',        'Cannot afford pet food this week.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1550, 38.7250), 4326), 3857), 'Campolide, Lisboa', 1),

-- MEDIUM
(19, 'Ride to appointment',             'Need transport to a clinic tomorrow morning.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1760, 38.6972), 4326), 3857), 'Belem, Lisboa', 1),

(20, 'Legal advice needed',             'Need guidance on housing rights.',
 (SELECT category_id FROM category WHERE name_cat='legal'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1450, 38.7050), 4326), 3857), 'Santos, Lisboa', 1),

(1,  'Tutoring for exam',               'Student needs math tutoring before final exam.',
 (SELECT category_id FROM category WHERE name_cat='education'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1500, 38.7180), 4326), 3857), 'Campo de Ourique, Lisboa', 1),

(2,  'Phone setup help',                'Elderly person needs help setting up a smartphone.',
 (SELECT category_id FROM category WHERE name_cat='tech'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1460, 38.7320), 4326), 3857), 'Lumiar, Lisboa', 1),

(3,  'Social companion needed',         'Isolated elderly woman needs weekly visit.',
 (SELECT category_id FROM category WHERE name_cat='social'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1380, 38.7350), 4326), 3857), 'Odivelas, Lisboa', 1),

(4,  'Shoes needed',                    'Child needs school shoes, size 34.',
 (SELECT category_id FROM category WHERE name_cat='clothing'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1510, 38.7220), 4326), 3857), 'Sete Rios, Lisboa', 1),

(5,  'Pet vet transport',               'Dog needs vet urgently, no car available.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1340, 38.7260), 4326), 3857), 'Xabregas, Lisboa', 1),

(6,  'Hygiene kit needed',              'Displaced person needs basic hygiene supplies.',
 (SELECT category_id FROM category WHERE name_cat='hygiene'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1420, 38.7220), 4326), 3857), 'Anjos, Lisboa', 1),

(7,  'Eldercare support',               'Elderly neighbour needs help with errands.',
 (SELECT category_id FROM category WHERE name_cat='eldercare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1350, 38.7080), 4326), 3857), 'Graca, Lisboa', 1),

(8,  'Translation help',                'Need Portuguese to English translation for documents.',
 (SELECT category_id FROM category WHERE name_cat='translation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1380, 38.7180), 4326), 3857), 'Martim Moniz, Lisboa', 1),

(9,  'Childcare support',               'Need someone to watch kids while at job interview.',
 (SELECT category_id FROM category WHERE name_cat='childcare'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1440, 38.7240), 4326), 3857), 'Arroios, Lisboa', 1),

(10, 'Small repair needed',             'Leaking tap needs fixing, landlord unresponsive.',
 (SELECT category_id FROM category WHERE name_cat='repairs'),
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1570, 38.7130), 4326), 3857), 'Camoes, Lisboa', 1),

-- LOW
(11, 'Help with online forms',          'Need help filling in government online forms.',
 (SELECT category_id FROM category WHERE name_cat='tech'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1427, 38.7108), 4326), 3857), 'Chiado, Lisboa', 1),

(12, 'Donation pickup',                 'Have furniture to donate, need collection.',
 (SELECT category_id FROM category WHERE name_cat='donation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1760, 38.6990), 4326), 3857), 'Restelo, Lisboa', 1),

(13, 'Help with CV',                    'Need help writing a CV in Portuguese.',
 (SELECT category_id FROM category WHERE name_cat='education'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1430, 38.7140), 4326), 3857), 'Intendente, Lisboa', 1),

(14, 'Cleaning supplies needed',        'Recently housed family needs a cleaning kit.',
 (SELECT category_id FROM category WHERE name_cat='hygiene'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1570, 38.7190), 4326), 3857), 'Carnide, Lisboa', 1),

(15, 'Storage space needed',            'Need to store a few boxes for two weeks.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1490, 38.7270), 4326), 3857), 'Telheiras, Lisboa', 1),

(16, 'Interpretation needed',           'Non-Portuguese speaker needs interpreter for appointment.',
 (SELECT category_id FROM category WHERE name_cat='translation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1360, 38.7310), 4326), 3857), 'Ameixoeira, Lisboa', 1),

(17, 'Companionship for elderly man',   'Widower looking for someone to play chess with weekly.',
 (SELECT category_id FROM category WHERE name_cat='social'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1530, 38.7060), 4326), 3857), 'Lapa, Lisboa', 1),

(18, 'Book donation needed',            'School needs second-hand textbooks for students.',
 (SELECT category_id FROM category WHERE name_cat='donation'),
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1620, 38.7220), 4326), 3857), 'Campolide, Lisboa', 1);

-- ─── OFFERS (Lisbon, all categories) ─────────────────────────────────────────

INSERT INTO offer (user_id, title, descrip, category, geom, address_point, status_id)
VALUES
(1,  'Grocery Delivery',           'Can deliver groceries within 2 hours.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1380, 38.7145), 4326), 3857), 'Baixa, Lisboa', 1),

(2,  'Food donations available',   'Can donate canned goods and dry food.',
 (SELECT category_id FROM category WHERE name_cat='food'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1500, 38.7090), 4326), 3857), 'Estrela, Lisboa', 1),

(3,  'Prescription Pickup',        'Can pick up prescriptions from any pharmacy in Lisbon.',
 (SELECT category_id FROM category WHERE name_cat='medical'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1400, 38.7130), 4326), 3857), 'Rossio, Lisboa', 1),

(4,  'Transport Assistance',       'Can drive to appointments on weekday mornings.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1750, 38.6980), 4326), 3857), 'Belem, Lisboa', 1),

(5,  'Friendly Call Check-ins',    'Can provide friendly phone check-ins this week.',
 (SELECT category_id FROM category WHERE name_cat='social'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1430, 38.7100), 4326), 3857), 'Chiado, Lisboa', 1),

(6,  'Emergency Shelter',          'Can host someone for one night in emergency.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1370, 38.7160), 4326), 3857), 'Mouraria, Lisboa', 1),

(7,  'Pet food available',         'Can share pet food with those in need.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1560, 38.7260), 4326), 3857), 'Campolide, Lisboa', 1),

(8,  'Clothing donations',         'Have warm jackets and shoes to donate.',
 (SELECT category_id FROM category WHERE name_cat='clothing'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1330, 38.7210), 4326), 3857), 'Intendente, Lisboa', 1),

(9,  'Hygiene supplies',           'Can provide hygiene kits and cleaning supplies.',
 (SELECT category_id FROM category WHERE name_cat='hygiene'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1430, 38.7230), 4326), 3857), 'Anjos, Lisboa', 1),

(10, 'Childcare available',        'Can babysit for short periods in emergencies.',
 (SELECT category_id FROM category WHERE name_cat='childcare'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1290, 38.7310), 4326), 3857), 'Mouraria, Lisboa', 1),

(11, 'Eldercare visits',           'Can visit and help elderly with shopping and errands.',
 (SELECT category_id FROM category WHERE name_cat='eldercare'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1360, 38.7090), 4326), 3857), 'Graca, Lisboa', 1),

(12, 'Home repairs',               'Handyman available for small urgent repairs.',
 (SELECT category_id FROM category WHERE name_cat='repairs'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1700, 38.7000), 4326), 3857), 'Belem, Lisboa', 1),

(13, 'Translation services',       'Fluent in English, Portuguese and French.',
 (SELECT category_id FROM category WHERE name_cat='translation'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1390, 38.7190), 4326), 3857), 'Martim Moniz, Lisboa', 1),

(14, 'Legal signposting',          'Law student, can help with basic legal questions.',
 (SELECT category_id FROM category WHERE name_cat='legal'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1460, 38.7060), 4326), 3857), 'Santos, Lisboa', 1),

(15, 'Tutoring available',         'Can tutor maths and sciences for secondary school.',
 (SELECT category_id FROM category WHERE name_cat='education'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1510, 38.7170), 4326), 3857), 'Campo de Ourique, Lisboa', 1),

(16, 'Tech help',                  'Can help with phones, online forms and government websites.',
 (SELECT category_id FROM category WHERE name_cat='tech'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1430, 38.7100), 4326), 3857), 'Chiado, Lisboa', 1),

(17, 'Listening support',          'Trained volunteer, available for conversations.',
 (SELECT category_id FROM category WHERE name_cat='mental_health'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1610, 38.7160), 4326), 3857), 'Amoreiras, Lisboa', 1),

(18, 'Donation collection',        'Can collect and deliver donated items.',
 (SELECT category_id FROM category WHERE name_cat='donation'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1750, 38.7010), 4326), 3857), 'Restelo, Lisboa', 1),

(19, 'Moving help',                'Can help pack and move boxes on weekends.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1420, 38.7280), 4326), 3857), 'Chelas, Lisboa', 1),

(20, 'Safety escort',              'Can escort people home safely in the evenings.',
 (SELECT category_id FROM category WHERE name_cat='safety'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1470, 38.7210), 4326), 3857), 'Intendente, Lisboa', 1),

(1,  'Shelter for one night',      'Can offer a spare room in emergency situations.',
 (SELECT category_id FROM category WHERE name_cat='shelter'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1350, 38.7190), 4326), 3857), 'Alfama, Lisboa', 1),

(2,  'Medical transport',          'Can drive patients to hospital appointments.',
 (SELECT category_id FROM category WHERE name_cat='transport'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1600, 38.7290), 4326), 3857), 'Benfica, Lisboa', 1),

(3,  'Vet transport',              'Can drive pets to the vet on weekday afternoons.',
 (SELECT category_id FROM category WHERE name_cat='pets'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1350, 38.7255), 4326), 3857), 'Xabregas, Lisboa', 1),

(4,  'Elderly companion',          'Happy to visit and keep elderly company weekly.',
 (SELECT category_id FROM category WHERE name_cat='eldercare'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1530, 38.7070), 4326), 3857), 'Lapa, Lisboa', 1),

(5,  'Storage available',          'Have a spare garage for short-term storage.',
 (SELECT category_id FROM category WHERE name_cat='logistics'),
 ST_Transform(ST_SetSRID(ST_MakePoint(-9.1500, 38.7260), 4326), 3857), 'Telheiras, Lisboa', 1);

-- ─── ASSIGNMENTS (mix of statuses) ───────────────────────────────────────────

INSERT INTO assignments (need_id, offer_id, status_ass, notes)
VALUES
(1,  3,  'accepted',   'Prescription pickup coordinated for this afternoon.'),
(2,  6,  'accepted',   'Emergency shelter confirmed for tonight.'),
(3,  1,  'proposed',   'Grocery delivery requested, awaiting confirmation.'),
(4,  10, 'accepted',   'Childcare arranged for two hours.'),
(5,  22, 'accepted',   'Ride to dialysis scheduled for tomorrow.'),
(9,  2,  'proposed',   'Grocery delivery offer matched to elderly resident.'),
(10, 8,  'accepted',   'Warm clothing collected and delivered.'),
(19, 4,  'accepted',   'Ride to clinic scheduled for tomorrow morning.'),
(20, 14, 'proposed',   'Legal guidance on housing rights requested.'),
(21, 15, 'accepted',   'Tutoring session arranged for Saturday.'),
(31, 16, 'completed',  'Help with online forms completed successfully.'),
(27, 13, 'completed',  'Translation of documents completed.'),
(15, 11, 'completed',  'Eldercare welfare check completed, all well.');

COMMIT;
