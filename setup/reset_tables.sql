-- Active: 1789483527172@@127.0.0.1@3306
DROP TABLE IF EXISTS skins;
DROP TABLE IF EXISTS skin_prices;
DROP TABLE IF EXISTS collection_names;
DROP TABLE IF EXISTS skin_types;

CREATE TABLE collection_names (
    collection_name VARCHAR(30) PRIMARY KEY
);

CREATE TABLE skin_types (
    skin_type VARCHAR(30) PRIMARY KEY
);

CREATE TABLE skins (
    skin_name VARCHAR(50) PRIMARY KEY,
    skin_type VARCHAR(30),
    stat_track BOOLEAN NULL,
    cagr DECIMAL(10, 6) NULL,
    collection_name VARCHAR(30) NOT NULL,
    CONSTRAINT fk_skin_type FOREIGN KEY (skin_type) REFERENCES skin_types(skin_type)
        ON DELETE CASCADE,
    CONSTRAINT fk_collection_name FOREIGN KEY (collection_name) REFERENCES collection_names(collection_name)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE skin_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skin_name VARCHAR(50) NOT NULL,
    skin_price DECIMAL(10, 2) NOT NULL,
    recorded_at DATETIME NOT NULL,
    CONSTRAINT fk_skin_name FOREIGN KEY (skin_name) REFERENCES skins(skin_name)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_skin_time UNIQUE (skin_name, recorded_at)
);

CREATE INDEX idx_prices_skin_name ON skin_prices(skin_name);
CREATE INDEX idx_prices_recorded_at ON skin_prices(recorded_at);
CREATE INDEX idx_collection_name ON skins(collection_name);
