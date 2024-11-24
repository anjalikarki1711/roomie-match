-- Sample Data
use roomie_match_db;

insert into user(user_id, name, gender, age, profession, location, profile_desc, pets, hobbies, seeking)
values(1, "Ella Bates", 'woman',24, 'researcher', 'Medford',
'I am a researcher who works from home, I like cooking and having people over at my place',
 'no', 'cooking, reading, watching TV', 'housing')


insert into user(user_id, name, gender, age, profession, location, profile_desc, pets, hobbies, seeking)
values(2, "Cal ", 'nonbinary',23, 'UX Designer', 'Sommerville',
'I am a creative, I appreciate personal space and privacy. I like crafting, painting and petting my cats',
'yes', 'Attending art exhibitions, drawing, winetasting', 'roommate')


insert into post(post_id, user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates, budget, housing_type, post_type)
values(4, 1, 'yes', 'no', 'yes', 5, 1300,'long-term-post-grad', 'housing')


insert into post(post_id, user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates, budget, housing_type, post_type)
values(6, 2, 'no', 'no', 'yes', 5, 1500,'long-term-post-grad', 'roommate')


insert into message(message_id, from, to, message_text, message_time)
values(7, 2, 1, 'Hi! I really like your apartment, are you still looking for roommates?', 2024-11-19 09:14:07)


insert into file(file_id, user_id, post_id, room_pic, profile_pic)
values(12, 1, null, null, ellaprofile.png) --just a profile picture


insert into file(file_id, user_id, post_id, room_pic, profile_pic)
values(20, 1, 4, ellaBapartmentpic1.png, ellaBprofile.png) --post files


insert into file(file_id, user_id, post_id, room_pic, profile_pic)
values(21, 1, 4, ellaBapartmentpic2.png, ellaBprofile.png) --post files