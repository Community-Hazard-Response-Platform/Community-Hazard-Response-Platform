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

INSERT INTO need (user_id, title, descrip, category, urgency, geom, address_point, status_id)
VALUES
(1,'Need medication today','Out of medication; urgent pickup needed.', 2,
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_GeomFromText('POINT(-1028000 4868000)', 3857),'Baixa, Lisboa',1),
(2,'Grocery delivery','Need groceries delivered for the next two days.', 1,
 (SELECT urgency_id FROM urgency_domain WHERE code='high'),
 ST_GeomFromText('POINT(-1028500 4868200)', 3857),'Chiado, Lisboa',1),
(3,'Ride to appointment','Need transport to a clinic tomorrow morning.', 3,
 (SELECT urgency_id FROM urgency_domain WHERE code='medium'),
 ST_GeomFromText('POINT(-1029000 4868500)', 3857),'Avenida da Liberdade, Lisboa',1),
(4,'Help with forms','Need help filling online forms.', 15,
 (SELECT urgency_id FROM urgency_domain WHERE code='low'),
 ST_GeomFromText('POINT(-1028700 4867900)', 3857),'Bairro Alto, Lisboa',1),
(5,'Temporary shelter','Need a safe place to stay tonight.', 5,
 (SELECT urgency_id FROM urgency_domain WHERE code='critical'),
 ST_GeomFromText('POINT(-1029500 4868300)', 3857),'Alfama, Lisboa',1);

INSERT INTO offer (user_id, title, descrip, category, geom, address_point, status_id)
VALUES
(1, 'Grocery Delivery', 'Can deliver groceries within 2 hours.', 1,
 ST_GeomFromText('POINT(-1028000 4868000)', 3857),'Baixa, Lisboa',1),
(2, 'Transport Assistance', 'Can drive to appointments (weekday mornings).', 2,
 ST_GeomFromText('POINT(-1028300 4868200)', 3857),'Chiado, Lisboa',1),
(3, 'Prescription Pickup', 'Can pick up prescriptions from pharmacies.', 3,
 ST_GeomFromText('POINT(-1029000 4868500)', 3857),'Avenida da Liberdade, Lisboa',1),
(4, 'Friendly Call Check-ins', 'Can provide friendly phone check-ins this week.', 4,
 ST_GeomFromText('POINT(-1028800 4867900)', 3857),'Bairro Alto, Lisboa',1),
(5, 'Emergency Shelter', 'Can host someone for one night (emergency).', 5,
 ST_GeomFromText('POINT(-1029600 4868300)', 3857),'Alfama, Lisboa',1);

INSERT INTO assignments (need_id, offer_id, status_ass, notes)
VALUES
(1, 3,'accepted','Prescription pickup coordinated.'),
(2, 1,'proposed','Groceries list requested.'),
(3, 2,'accepted','Ride scheduled for tomorrow morning.'),
(4, 5,'proposed','Will help with online form submission.'),
(5, 4,'accepted','Emergency accommodation offered.');


COMMIT;
