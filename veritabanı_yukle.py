import pymysql


connection = pymysql.connect(
    host='mysql-289e9598-eralpyayalikk-4fe5.h.aivencloud.com',
    port=26850,
    user='avnadmin',
    password='AVNS_hG58TwM77PFReskocjL', 
    database='film_arsivi',
    ssl={'ca': None}, 
    connect_timeout=20   
)

sql_script = """
CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  `email` text NOT NULL,
  `username` text NOT NULL,
  `password` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `bio` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `comments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `movie_id` int(11) NOT NULL,
  `username` varchar(100) DEFAULT NULL,
  `comment_text` text NOT NULL,
  `rating` int(11) DEFAULT 5,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `movie_title` varchar(255) DEFAULT NULL,
  `movie_poster` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `favorites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `movie_id` int(11) NOT NULL,
  `movie_title` varchar(255) DEFAULT NULL,
  `movie_poster` varchar(255) DEFAULT NULL,
  `comment` text DEFAULT NULL,
  `rating` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `user_lists` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `list_name` varchar(255) NOT NULL,
  `movie_id` int(11) NOT NULL,
  `movie_title` varchar(255) DEFAULT NULL,
  `movie_poster` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Verileri ekleyelim (Senin attığın yorumlardan birkaçı örnek olarak)
INSERT IGNORE INTO `users` (`id`, `name`, `email`, `username`, `password`) VALUES
(1, 'Eralp Yayalık', 'eralpfb99@gmail.com', 'eralp', '$5$rounds=535000$0HLHAmPLFhgW9vFt$1dJ6nXNnktdmZo.BUm2sE7F7UWekHrG4L/gMYjsqdZ0');

INSERT IGNORE INTO `comments` (`id`, `user_id`, `movie_id`, `username`, `comment_text`, `rating`, `movie_title`) VALUES
(6, 1, 754, 'eralp', 'bu ne la böle çöp', 5, 'Yüz/Yüze');
"""

try:
    with connection.cursor() as cursor:
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
    connection.commit()
    print("Veritabanı başarıyla Aiven'a taşındı! Siten artık hazır knk! 🚀")
except Exception as e:
    print(f"Hata oluştu: {e}")
finally:
    connection.close()