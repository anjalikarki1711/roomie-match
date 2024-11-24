-- Creates the tables required
use roomie_match_db;

-- drop table if exists file;
-- drop table if exists message;
-- drop table if exists post;
-- drop table if exists user;


-- CREATE TABLE user (
--   user_id int PRIMARY KEY,
--   name varchar(60),
--   gender enum('man','woman','nonbinary'),
--   age int,
--   profession varchar(50),
--   location varchar(50),
--   profile_desc varchar(200),
--   pets enum('yes','no'),
--   hobbies varchar(70),
--   seeking enum('roommate', 'housing')
-- )
-- ENGINE = InnoDB;
-- CREATE TABLE post (
--   post_id int PRIMARY KEY,
--   user_id int,
--   shared_bathroom enum('yes','no'),
--   shared_bedroom enum('yes','no'),
--   ok_with_pets enum('yes','no'),
--   max_roommates int,
--   budget int,
--   housing_type enum('summer','long-term-post-grad', 'winter','short-term'),
--   post_type enum('housing', 'roommate'),
--   FOREIGN KEY (user_id) REFERENCES user(user_id)
-- )
-- ENGINE = InnoDB;
-- CREATE TABLE message (
--   message_id int PRIMARY KEY,
--   from int,
--   to int,
--   message_text varchar(200),
--   message_time timestamp,
--   FOREIGN KEY (from) REFERENCES user (user_id),
--   FOREIGN KEY (to) REFERENCES user (user_id)
-- )
-- ENGINE = InnoDB;
-- CREATE TABLE file (
--   file_id int PRIMARY KEY,
--   user_id int,
--   post_id int,
--   room_pic blob,
--   profile_pic blob,
--   FOREIGN KEY (user_id) REFERENCES user (user_id),
--   FOREIGN KEY (post_id) REFERENCES post (post_id)
-- )
-- ENGINE = InnoDB;

-- ALTER TABLE message
-- MODIFY COLUMN message_id int not null auto_increment;

-- update message
-- set message_id = 1 where message_id = 7;
-- update message 
-- set message_id = 2 where message_id = 8;

-- ALTER TABLE user
-- MODIFY COLUMN user_id int not null auto_increment;

-- ALTER TABLE `file`
-- MODIFY COLUMN file_id int not null auto_increment;

ALTER TABLE post
MODIFY COLUMN post_id int not null auto_increment;





