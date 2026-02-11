CREATE EXTENSION IF NOT EXISTS postgis;

-- Tables
DROP TRIGGER IF EXISTS trg_prevent_invalid_assignment ON assignments;
DROP TRIGGER IF EXISTS trg_assignment_update_completed ON assignments;
DROP TRIGGER IF EXISTS trg_assignment_insert_sync_status ON assignments;
DROP TRIGGER IF EXISTS update_offer_updated_at ON offer;
DROP TRIGGER IF EXISTS update_need_updated_at ON need;

DROP FUNCTION IF EXISTS prevent_invalid_assignment();
DROP FUNCTION IF EXISTS sync_status_on_assignment_completed();
DROP FUNCTION IF EXISTS sync_status_on_assignment_insert();
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP TABLE IF EXISTS assignments CASCADE;
DROP TABLE IF EXISTS offer CASCADE;
DROP TABLE IF EXISTS need CASCADE;

DROP TABLE IF EXISTS facility CASCADE;
DROP TABLE IF EXISTS administrative_area CASCADE;

DROP TABLE IF EXISTS urgency_domain CASCADE;
DROP TABLE IF EXISTS status_domain CASCADE;
DROP TABLE IF EXISTS category CASCADE;

DROP TABLE IF EXISTS app_user CASCADE;

-- App Users
CREATE TABLE app_user (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- Categories of needs/offers (e.g., 'food', 'medical', 'transport', 'social')
CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    name_cat VARCHAR(100) NOT NULL,                
    descrip TEXT
);


-- Predifined status values for needs/offers (e.g., 'active', 'assigned', 'resolved')
CREATE TABLE status_domain (
  status_id  SERIAL PRIMARY KEY,
  code       VARCHAR(20) UNIQUE NOT NULL,
  name       VARCHAR(50) NOT NULL
);

-- Allowed values
INSERT INTO status_domain (code, name) VALUES
  ('active',   'Active'),
  ('assigned', 'Assigned'),
  ('resolved', 'Resolved');


-- Urgency levels for needs (e.g., 'critical', 'high', 'medium', 'low')
CREATE TABLE urgency_domain (
  urgency_id SERIAL PRIMARY KEY,
  code       VARCHAR(20) UNIQUE NOT NULL,
  name       VARCHAR(50) NOT NULL
);

-- Allowed values
INSERT INTO urgency_domain (code, name) VALUES
  ('critical', 'Critical'),
  ('high',     'High'),
  ('medium',   'Medium'),
  ('low',      'Low');



-- Needs (requests for help)
CREATE TABLE need (
    need_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    descrip TEXT NOT NULL,
    category INTEGER NOT NULL,
    urgency INTEGER NOT NULL DEFAULT (SELECT urgency_id FROM urgency_domain WHERE code = 'medium'),
    geom GEOMETRY(Point, 3857) NOT NULL,
    address_point VARCHAR(500),
    status_id INTEGER NOT NULL DEFAULT (SELECT status_id FROM status_domain WHERE code = 'active'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_need_user FOREIGN KEY (user_id) REFERENCES app_user(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_need_category FOREIGN KEY (category) REFERENCES category(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_need_status FOREIGN KEY (status_id) REFERENCES status_domain(status_id) ON DELETE RESTRICT,
    CONSTRAINT fk_need_urgency FOREIGN KEY (urgency) REFERENCES urgency_domain(urgency_id) ON DELETE RESTRICT
);

-- Offers (volunteer availability)
CREATE TABLE offer (
    offer_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    descrip TEXT NOT NULL,
    category INTEGER NOT NULL,
    geom GEOMETRY(Point, 3857),
    address_point VARCHAR(500),
    status_id INTEGER NOT NULL DEFAULT (SELECT status_id FROM status_domain WHERE code = 'active'),    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_offer_user FOREIGN KEY (user_id) REFERENCES app_user(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_offer_category FOREIGN KEY (category) REFERENCES category(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_offer_status FOREIGN KEY (status_id) REFERENCES status_domain(status_id) ON DELETE RESTRICT   
);

-- Assignments (matching needs with offers)
CREATE TABLE assignments (
    assignment_id SERIAL PRIMARY KEY,
    need_id INTEGER UNIQUE NOT NULL,
    offer_id INTEGER UNIQUE NOT NULL,
    status_ass VARCHAR(20) NOT NULL DEFAULT 'proposed' CHECK (status_ass IN ('proposed', 'accepted', 'rejected', 'completed')),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    CONSTRAINT fk_need_assignment FOREIGN KEY (need_id) REFERENCES need(need_id) ON DELETE CASCADE,
    CONSTRAINT fk_offer_assignment FOREIGN KEY (offer_id) REFERENCES offer(offer_id) ON DELETE CASCADE
);


-- Tables from OSM

-- Administrative Areas (from OSM)
CREATE TABLE administrative_area (
    area_id SERIAL PRIMARY KEY,
    name_area VARCHAR(100) NOT NULL,
    admin_level INTEGER NOT NULL,
    geom GEOMETRY(Polygon, 3857) NOT NULL
);

-- Emergency Facilities (from OSM)
CREATE TABLE facility (
    facility_id SERIAL PRIMARY KEY,
    osm_id BIGINT,
    name_fac VARCHAR(255),
    facility_type VARCHAR(50) NOT NULL,
    geom GEOMETRY(Point, 3857) NOT NULL
);


-- triggers

-- spatial queries on needs (e.g., "needs within 5km")
CREATE INDEX idx_need_geom ON need USING GIST (geom);

-- spatial queries on offers (e.g., "offers near a point")
CREATE INDEX idx_offer_geom ON offer USING GIST (geom);

-- filtering by administrative area (e.g., "needs in Lisbon")
CREATE INDEX idx_admin_area_geom ON administrative_area USING GIST (geom);

-- finding nearby facilities (e.g., "hospitals near a need")
CREATE INDEX idx_facility_geom ON facility USING GIST (geom);

-- triggers for updated_at timestamps


-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for need table
DROP TRIGGER IF EXISTS update_need_updated_at ON need;
CREATE TRIGGER update_need_updated_at
    BEFORE UPDATE ON need
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for offer table
DROP TRIGGER IF EXISTS update_offer_updated_at ON offer;
CREATE TRIGGER update_offer_updated_at
    BEFORE UPDATE ON offer
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Trigger to sync status of need and offer when an assignment is created, "assigned" status is set
CREATE OR REPLACE FUNCTION sync_status_on_assignment_insert()
RETURNS TRIGGER AS $$
BEGIN
  -- Set need to assigned
  UPDATE need
  SET status_id = (SELECT status_id FROM status_domain WHERE code='assigned')
  WHERE need_id = NEW.need_id;

  -- Set offer to assigned
  UPDATE offer
  SET status_id = (SELECT status_id FROM status_domain WHERE code='assigned')
  WHERE offer_id = NEW.offer_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_assignment_insert_sync_status ON assignments;
CREATE TRIGGER trg_assignment_insert_sync_status
AFTER INSERT ON assignments
FOR EACH ROW
EXECUTE FUNCTION sync_status_on_assignment_insert();


-- Trigger to sync status of need and offer when an assignment is marked as completed, "resolved" status is set
CREATE OR REPLACE FUNCTION sync_status_on_assignment_completed()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status_ass = 'completed' AND OLD.status_ass IS DISTINCT FROM NEW.status_ass THEN
    UPDATE need
    SET status_id = (SELECT status_id FROM status_domain WHERE code='resolved')
    WHERE need_id = NEW.need_id;

    UPDATE offer
    SET status_id = (SELECT status_id FROM status_domain WHERE code='resolved')
    WHERE offer_id = NEW.offer_id;

    -- also stamp completion time if not set
    IF NEW.completed_at IS NULL THEN
      NEW.completed_at = NOW();
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_assignment_update_completed ON assignments;
CREATE TRIGGER trg_assignment_update_completed
BEFORE UPDATE OF status_ass ON assignments
FOR EACH ROW
EXECUTE FUNCTION sync_status_on_assignment_completed();

-- Trigger to prevent assigning needs/offers that are not active
CREATE OR REPLACE FUNCTION prevent_invalid_assignment()
RETURNS TRIGGER AS $$
DECLARE
  need_status TEXT;
  offer_status TEXT;
BEGIN
  SELECT s.code INTO need_status
  FROM need n JOIN status_domain s ON s.status_id = n.status_id
  WHERE n.need_id = NEW.need_id;

  SELECT s.code INTO offer_status
  FROM offer o JOIN status_domain s ON s.status_id = o.status_id
  WHERE o.offer_id = NEW.offer_id;

  IF need_status IS DISTINCT FROM 'active' THEN
    RAISE EXCEPTION 'Need % cannot be assigned because status is %', NEW.need_id, need_status;
  END IF;

  IF offer_status IS DISTINCT FROM 'active' THEN
    RAISE EXCEPTION 'Offer % cannot be assigned because status is %', NEW.offer_id, offer_status;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_invalid_assignment ON assignments;
CREATE TRIGGER trg_prevent_invalid_assignment
BEFORE INSERT ON assignments
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_assignment();
