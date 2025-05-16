CREATE TABLE users (
    login VARCHAR(255) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL
);

CREATE TABLE collections (
    uuid UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_login VARCHAR(255) NOT NULL,

    FOREIGN KEY (user_login) 
        REFERENCES users(login)
        ON DELETE CASCADE
);

CREATE TABLE books (
    uuid UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    file_name VARCHAR(255),
    collection_uuid UUID NOT NULL,

    FOREIGN KEY (collection_uuid) 
        REFERENCES collections(uuid)
        ON DELETE CASCADE
);
