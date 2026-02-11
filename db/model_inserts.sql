BEGIN;

TRUNCATE TABLE assignments RESTART IDENTITY CASCADE;
TRUNCATE TABLE offer RESTART IDENTITY CASCADE;
TRUNCATE TABLE need RESTART IDENTITY CASCADE;
TRUNCATE TABLE facility RESTART IDENTITY CASCADE;
TRUNCATE TABLE administrative_area RESTART IDENTITY CASCADE;
TRUNCATE TABLE category RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_user RESTART IDENTITY CASCADE;

INSERT INTO app_user (username, email, hashed_password, firstname, surname, phone, is_verified) VALUES
('user01','user01@example.com','$2b$12$dummyhash01','Alex','Silva',     '+351910000001', TRUE),
('user02','user02@example.com','$2b$12$dummyhash02','Bea','Costa',      '+351910000002', TRUE),
('user03','user03@example.com','$2b$12$dummyhash03','Carla','Ramos',    '+351910000003', FALSE),
('user04','user04@example.com','$2b$12$dummyhash04','Diogo','Pereira',  '+351910000004', TRUE),
('user05','user05@example.com','$2b$12$dummyhash05','Eva','Almeida',    '+351910000005', TRUE),
('user06','user06@example.com','$2b$12$dummyhash06','Filipe','Rocha',   '+351910000006', FALSE),
('user07','user07@example.com','$2b$12$dummyhash07','Gabi','Santos',    '+351910000007', TRUE),
('user08','user08@example.com','$2b$12$dummyhash08','Hugo','Ferreira',  '+351910000008', TRUE),
('user09','user09@example.com','$2b$12$dummyhash09','Ines','Carvalho',  '+351910000009', FALSE),
('user10','user10@example.com','$2b$12$dummyhash10','Joao','Martins',   '+351910000010', TRUE),
('user11','user11@example.com','$2b$12$dummyhash11','Katia','Lopes',    '+351910000011', TRUE),
('user12','user12@example.com','$2b$12$dummyhash12','Luis','Gomes',     '+351910000012', TRUE),
('user13','user13@example.com','$2b$12$dummyhash13','Marta','Sousa',    '+351910000013', FALSE),
('user14','user14@example.com','$2b$12$dummyhash14','Nuno','Neves',     '+351910000014', TRUE),
('user15','user15@example.com','$2b$12$dummyhash15','Olga','Correia',   '+351910000015', TRUE),
('user16','user16@example.com','$2b$12$dummyhash16','Paulo','Teixeira', '+351910000016', FALSE),
('user17','user17@example.com','$2b$12$dummyhash17','Rita','Nogueira',  '+351910000017', TRUE),
('user18','user18@example.com','$2b$12$dummyhash18','Sara','Araujo',    '+351910000018', TRUE),
('user19','user19@example.com','$2b$12$dummyhash19','Tiago','Mendes',   '+351910000019', FALSE),
('user20','user20@example.com','$2b$12$dummyhash20','Vasco','Pinto',    '+351910000020', TRUE);

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

INSERT INTO administrative_area (name_area, admin_level, geom) VALUES
('Test Area 01', 8,  ST_GeomFromText('POLYGON(( -20000 -20000, -10000 -20000, -10000 -10000, -20000 -10000, -20000 -20000 ))', 3857)),
('Test Area 02', 8,  ST_GeomFromText('POLYGON(( -10000 -20000,      0 -20000,      0 -10000, -10000 -10000, -10000 -20000 ))', 3857)),
('Test Area 03', 8,  ST_GeomFromText('POLYGON((      0 -20000,  10000 -20000,  10000 -10000,      0 -10000,      0 -20000 ))', 3857)),
('Test Area 04', 8,  ST_GeomFromText('POLYGON((  10000 -20000,  20000 -20000,  20000 -10000,  10000 -10000,  10000 -20000 ))', 3857)),
('Test Area 05', 8,  ST_GeomFromText('POLYGON(( -20000 -10000, -10000 -10000, -10000      0, -20000      0, -20000 -10000 ))', 3857)),
('Test Area 06', 8,  ST_GeomFromText('POLYGON(( -10000 -10000,      0 -10000,      0      0, -10000      0, -10000 -10000 ))', 3857)),
('Test Area 07', 8,  ST_GeomFromText('POLYGON((      0 -10000,  10000 -10000,  10000      0,      0      0,      0 -10000 ))', 3857)),
('Test Area 08', 8,  ST_GeomFromText('POLYGON((  10000 -10000,  20000 -10000,  20000      0,  10000      0,  10000 -10000 ))', 3857)),
('Test Area 09', 9,  ST_GeomFromText('POLYGON(( -20000      0, -10000      0, -10000  10000, -20000  10000, -20000      0 ))', 3857)),
('Test Area 10', 9,  ST_GeomFromText('POLYGON(( -10000      0,      0      0,      0  10000, -10000  10000, -10000      0 ))', 3857)),
('Test Area 11', 9,  ST_GeomFromText('POLYGON((      0      0,  10000      0,  10000  10000,      0  10000,      0      0 ))', 3857)),
('Test Area 12', 9,  ST_GeomFromText('POLYGON((  10000      0,  20000      0,  20000  10000,  10000  10000,  10000      0 ))', 3857)),
('Test Area 13', 10, ST_GeomFromText('POLYGON(( -20000  10000, -10000  10000, -10000  20000, -20000  20000, -20000  10000 ))', 3857)),
('Test Area 14', 10, ST_GeomFromText('POLYGON(( -10000  10000,      0  10000,      0  20000, -10000  20000, -10000  10000 ))', 3857)),
('Test Area 15', 10, ST_GeomFromText('POLYGON((      0  10000,  10000  10000,  10000  20000,      0  20000,      0  10000 ))', 3857)),
('Test Area 16', 10, ST_GeomFromText('POLYGON((  10000  10000,  20000  10000,  20000  20000,  10000  20000,  10000  10000 ))', 3857)),
('Test Area 17', 8,  ST_GeomFromText('POLYGON((  22000 -12000,  32000 -12000,  32000  -2000,  22000  -2000,  22000 -12000 ))', 3857)),
('Test Area 18', 8,  ST_GeomFromText('POLYGON((  22000   2000,  32000   2000,  32000  12000,  22000  12000,  22000   2000 ))', 3857)),
('Test Area 19', 8,  ST_GeomFromText('POLYGON(( -32000 -12000, -22000 -12000, -22000  -2000, -32000  -2000, -32000 -12000 ))', 3857)),
('Test Area 20', 8,  ST_GeomFromText('POLYGON(( -32000   2000, -22000   2000, -22000  12000, -32000  12000, -32000   2000 ))', 3857));

INSERT INTO facility (osm_id, name_fac, facility_type, geom) VALUES
(910000001,'Hospital Alpha','hospital',              ST_GeomFromText('POINT(  5000  3000)',3857)),
(910000002,'Hospital Beta','hospital',               ST_GeomFromText('POINT( 15000  2000)',3857)),
(910000003,'Clinic Gamma','clinic',                  ST_GeomFromText('POINT( -8000  2500)',3857)),
(910000004,'Clinic Delta','clinic',                  ST_GeomFromText('POINT( 26000  9000)',3857)),
(910000005,'Fire Station 1','fire_station',          ST_GeomFromText('POINT( -4000  2000)',3857)),
(910000006,'Fire Station 2','fire_station',          ST_GeomFromText('POINT( 12000 -7000)',3857)),
(910000007,'Police 1','police',                      ST_GeomFromText('POINT(  2000 -6000)',3857)),
(910000008,'Police 2','police',                      ST_GeomFromText('POINT(-14000 -3000)',3857)),
(910000009,'Shelter One','shelter',                  ST_GeomFromText('POINT(-12000 -2000)',3857)),
(910000010,'Shelter Two','shelter',                  ST_GeomFromText('POINT( 18000 11000)',3857)),
(910000011,'Pharmacy A','pharmacy',                  ST_GeomFromText('POINT(  5200  2800)',3857)),
(910000012,'Pharmacy B','pharmacy',                  ST_GeomFromText('POINT( -2000  1000)',3857)),
(910000013,'Food Bank 1','food_bank',                ST_GeomFromText('POINT(  1000  -800)',3857)),
(910000014,'Food Bank 2','food_bank',                ST_GeomFromText('POINT( 21000  -500)',3857)),
(910000015,'Community Center 1','community_centre',  ST_GeomFromText('POINT( -6000  9000)',3857)),
(910000016,'Community Center 2','community_centre',  ST_GeomFromText('POINT(  8000 14000)',3857)),
(910000017,'Vet Clinic 1','veterinary',              ST_GeomFromText('POINT(  7800 -2100)',3857)),
(910000018,'Vet Clinic 2','veterinary',              ST_GeomFromText('POINT(-18000  6000)',3857)),
(910000019,'Ambulance Base','ambulance_station',     ST_GeomFromText('POINT(  9000  5000)',3857)),
(910000020,'Emergency Post','emergency_service',     ST_GeomFromText('POINT( -9000 -9000)',3857));

INSERT INTO need (user_id, title, descrip, category, urgency, geom, address_point) VALUES
( 1,'Need medication today','Out of medication; urgent pickup needed.',            2,(SELECT urgency_id FROM urgency_domain WHERE code='critical'), ST_GeomFromText('POINT(  4500  3200)',3857),'Address N01'),
( 2,'Grocery delivery','Need groceries delivered for the next two days.',          1,(SELECT urgency_id FROM urgency_domain WHERE code='high'),     ST_GeomFromText('POINT(  1200  -800)',3857),'Address N02'),
( 3,'Ride to appointment','Need transport to a clinic tomorrow morning.',          3,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),   ST_GeomFromText('POINT( -3000  1800)',3857),'Address N03'),
( 4,'Help with forms','Need help filling online forms.',                           15,(SELECT urgency_id FROM urgency_domain WHERE code='low'),     ST_GeomFromText('POINT( 26000  1000)',3857),'Address N04'),
( 5,'Temporary shelter','Need a safe place to stay tonight.',                      5,(SELECT urgency_id FROM urgency_domain WHERE code='critical'), ST_GeomFromText('POINT(-15000 -5000)',3857),'Address N05'),
( 6,'Pet food','Need cat food for one week.',                                      6,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),   ST_GeomFromText('POINT(  8000 -2000)',3857),'Address N06'),
( 7,'Warm clothing','Need a winter coat and shoes.',                               7,(SELECT urgency_id FROM urgency_domain WHERE code='high'),     ST_GeomFromText('POINT( -9000  5000)',3857),'Address N07'),
( 8,'Hygiene kit','Need hygiene supplies (soap, shampoo, diapers).',               8,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),   ST_GeomFromText('POINT(  2000  9000)',3857),'Address N08'),
( 9,'Childcare support','Need 2 hours of childcare for an emergency.',             9,(SELECT urgency_id FROM urgency_domain WHERE code='high'),     ST_GeomFromText('POINT( 11000  2500)',3857),'Address N09'),
(10,'Eldercare check-in','Need someone to check in on an elderly neighbor.',       10,(SELECT urgency_id FROM urgency_domain WHERE code='low'),     ST_GeomFromText('POINT(  6000 12000)',3857),'Address N10'),
(11,'Small home repair','Broken door lock needs quick fix.',                       11,(SELECT urgency_id FROM urgency_domain WHERE code='high'),    ST_GeomFromText('POINT( 17000 -3000)',3857),'Address N11'),
(12,'Translation help','Need translation for a medical call.',                     12,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),  ST_GeomFromText('POINT( -7000 -6000)',3857),'Address N12'),
(13,'Legal signposting','Need help understanding a letter.',                       13,(SELECT urgency_id FROM urgency_domain WHERE code='low'),     ST_GeomFromText('POINT(  3000 -12000)',3857),'Address N13'),
(14,'Tutoring','Need math tutoring for a student.',                                14,(SELECT urgency_id FROM urgency_domain WHERE code='low'),     ST_GeomFromText('POINT( -2000  7000)',3857),'Address N14'),
(15,'Mental health support','Need someone to talk to today.',                      16,(SELECT urgency_id FROM urgency_domain WHERE code='high'),    ST_GeomFromText('POINT(  9000  1000)',3857),'Address N15'),
(16,'Donation pickup','Need help picking up donated items.',                       17,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),  ST_GeomFromText('POINT( 21000  8000)',3857),'Address N16'),
(17,'Moving essentials','Need help packing and moving boxes.',                      18,(SELECT urgency_id FROM urgency_domain WHERE code='medium'),  ST_GeomFromText('POINT( 24000 -6000)',3857),'Address N17'),
(18,'Safety escort','Need escort walking home late.',                               19,(SELECT urgency_id FROM urgency_domain WHERE code='high'),    ST_GeomFromText('POINT( -5000  2000)',3857),'Address N18'),
(19,'Misc urgent request','Need miscellaneous help urgently.',                      20,(SELECT urgency_id FROM urgency_domain WHERE code='critical'),ST_GeomFromText('POINT( -12000 11000)',3857),'Address N19'),
(20,'Food and water','Need food and drinking water for today.',                     1,(SELECT urgency_id FROM urgency_domain WHERE code='critical'),ST_GeomFromText('POINT( 14000 -9000)',3857),'Address N20');

INSERT INTO offer (user_id, descrip, category, geom) VALUES
( 1,'Can deliver groceries within 2 hours.',                 1, ST_GeomFromText('POINT(  1500  -500)',3857)),
( 2,'Can drive to appointments (weekday mornings).',         3, ST_GeomFromText('POINT( -2500  1600)',3857)),
( 3,'Can pick up prescriptions from pharmacies.',            2, ST_GeomFromText('POINT(  5200  2800)',3857)),
( 4,'Can provide friendly phone check-ins this week.',       4, NULL),
( 5,'Can host someone for one night (emergency).',           5, ST_GeomFromText('POINT(-14000 -4500)',3857)),
( 6,'Can help with pet transport to the vet.',               6, ST_GeomFromText('POINT(  7800 -2100)',3857)),
( 7,'Can donate warm clothes (sizes M/L).',                  7, ST_GeomFromText('POINT( -8000  5200)',3857)),
( 8,'Can assemble hygiene kits and deliver.',                8, ST_GeomFromText('POINT(  2200  8800)',3857)),
( 9,'Can provide short childcare support (2h).',             9, ST_GeomFromText('POINT( 11500  2600)',3857)),
(10,'Can do elder visits and small errands.',               10, ST_GeomFromText('POINT(  6500 11800)',3857)),
(11,'Can do small home repairs (basic tools).',             11, ST_GeomFromText('POINT( 17500 -2800)',3857)),
(12,'Can help translate PT/EN on calls.',                   12, ST_GeomFromText('POINT( -7200 -5900)',3857)),
(13,'Can help read letters and explain options.',           13, ST_GeomFromText('POINT(  2800 -11800)',3857)),
(14,'Can tutor math for 1 hour sessions.',                  14, ST_GeomFromText('POINT( -2500  6800)',3857)),
(15,'Can offer listening support and signposting.',         16, ST_GeomFromText('POINT(  8800  1200)',3857)),
(16,'Can help coordinate donation pickup/drop-off.',        17, ST_GeomFromText('POINT( 20500  7800)',3857)),
(17,'Can help pack boxes and move light items.',            18, ST_GeomFromText('POINT( 23500 -6100)',3857)),
(18,'Can escort someone for safety (evening).',             19, ST_GeomFromText('POINT( -5200  2100)',3857)),
(19,'Can deliver water and basic supplies.',                 1, ST_GeomFromText('POINT( 13800 -9200)',3857)),
(20,'Can do tech help: phones, accounts, online forms.',    15, ST_GeomFromText('POINT( 26000   900)',3857));


INSERT INTO assignments (need_id, offer_id, status_ass, notes) VALUES
( 1,  3,'accepted',  'Prescription pickup coordinated.'),
( 2,  1,'proposed',  'Groceries list requested.'),
( 3,  2,'accepted',  'Ride scheduled for tomorrow morning.'),
( 4, 20,'proposed',  'Will help with online form submission.'),
( 5,  5,'accepted',  'Emergency accommodation offered.'),
( 6,  6,'proposed',  'Vet transport time to be confirmed.'),
( 7,  7,'accepted',  'Clothes drop-off arranged.'),
( 8,  8,'proposed',  'Hygiene kit delivery window pending.'),
( 9,  9,'accepted',  'Childcare agreed for 2 hours.'),
(10, 10,'proposed',  'Check-in scheduled for afternoon.'),
(11, 11,'accepted',  'Repair visit scheduled.'),
(12, 12,'proposed',  'Call translation time pending.'),
(13, 13,'accepted',  'Letter review appointment set.'),
(14, 14,'proposed',  'Tutoring session planned.'),
(15, 15,'accepted',  'Support call scheduled today.'),
(16, 16,'proposed',  'Donation pickup route planning.'),
(17, 17,'accepted',  'Packing help arranged.'),
(18, 18,'proposed',  'Escort details');

COMMIT;
