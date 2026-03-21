
CREATE EXTENSION IF NOT EXISTS ltree;

-- DELETE FROM off_category_paths;
-- DELETE FROM off_category_names;
-- DELETE FROM off_category_synonyms;
-- DELETE FROM off_category;

CREATE TABLE IF NOT EXISTS off_category (
    code varchar NOT NULL,
    fallback_language varchar,
    CONSTRAINT off_category_pkey PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS off_category_paths (
    code varchar NOT NULL,
    tree ltree NOT NULL,
    CONSTRAINT off_category_paths_pkey PRIMARY KEY (code, tree),
    CONSTRAINT off_category_paths_code_fkey
        FOREIGN KEY (code)
        REFERENCES off_category (code)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS off_category_names (
    code varchar NOT NULL,
    language varchar NOT NULL,
    name varchar NOT NULL,
    CONSTRAINT off_category_names_pkey
        PRIMARY KEY (code, language),
    CONSTRAINT off_category_names_code_fkey
        FOREIGN KEY (code)
        REFERENCES off_category (code)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS off_category_synonyms (
    code varchar NOT NULL,
    language varchar NOT NULL,
    synonym varchar NOT NULL,
    CONSTRAINT off_category_synonyms_pkey
        PRIMARY KEY (code, language, synonym),
    CONSTRAINT off_category_synonyms_code_fkey
        FOREIGN KEY (code)
        REFERENCES off_category (code)
        ON DELETE CASCADE
);