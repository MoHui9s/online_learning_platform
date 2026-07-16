"""18 core tables — reproduction migration.

Generates the same schema as docs/database-schema.md without relying on the
ORM models, so any checkout that runs `alembic upgrade head` reproduces the
identical database (column types, indexes, FKs) on a fresh volume.

Revision ID: 0001
Revises:
Create Date: 2026-07-16

"""
from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.execute("""
    CREATE TABLE users (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        username VARCHAR(64) NOT NULL,
        email VARCHAR(128) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin','teacher','student') NOT NULL DEFAULT 'student',
        nickname VARCHAR(64) NULL,
        avatar_url VARCHAR(512) NULL,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_username (username),
        UNIQUE KEY uk_email (email),
        KEY idx_role (role)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # categories
    op.execute("""
    CREATE TABLE categories (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name VARCHAR(64) NOT NULL,
        parent_id BIGINT UNSIGNED NULL,
        sort_order INT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_parent_id (parent_id),
        UNIQUE KEY uk_parent_name (parent_id, name),
        CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # courses
    op.execute("""
    CREATE TABLE courses (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        title VARCHAR(200) NOT NULL,
        description TEXT NULL,
        cover_url VARCHAR(512) NULL,
        category_id BIGINT UNSIGNED NULL,
        teacher_id BIGINT UNSIGNED NOT NULL,
        status ENUM('draft','published','offline') NOT NULL DEFAULT 'draft',
        price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        student_count INT UNSIGNED NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_teacher_id (teacher_id),
        KEY idx_category_id (category_id),
        KEY idx_status (status),
        CONSTRAINT fk_courses_category FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
        CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # chapters
    op.execute("""
    CREATE TABLE chapters (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id BIGINT UNSIGNED NOT NULL,
        parent_id BIGINT UNSIGNED NULL,
        title VARCHAR(200) NOT NULL,
        sort_order INT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_chapters_course_id (course_id),
        KEY idx_chapters_parent_id (parent_id),
        CONSTRAINT fk_chapters_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_chapters_parent FOREIGN KEY (parent_id) REFERENCES chapters (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # courseware
    op.execute("""
    CREATE TABLE courseware (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        chapter_id BIGINT UNSIGNED NOT NULL,
        title VARCHAR(200) NOT NULL,
        type ENUM('video','pdf','ppt','doc') NOT NULL,
        file_path VARCHAR(512) NOT NULL,
        file_name VARCHAR(255) NULL,
        file_size BIGINT UNSIGNED NULL,
        mime_type VARCHAR(128) NULL,
        duration INT UNSIGNED NULL,
        sort_order INT NOT NULL DEFAULT 0,
        uploaded_by BIGINT UNSIGNED NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_courseware_chapter_id (chapter_id),
        KEY idx_courseware_type (type),
        KEY idx_courseware_uploaded_by (uploaded_by),
        CONSTRAINT fk_courseware_chapter FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE,
        CONSTRAINT fk_courseware_uploader FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # enrollments
    op.execute("""
    CREATE TABLE enrollments (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        course_id BIGINT UNSIGNED NOT NULL,
        status ENUM('active','completed','dropped') NOT NULL DEFAULT 'active',
        progress_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
        enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_enrollments_user_course (user_id, course_id),
        KEY idx_enrollments_course_id (course_id),
        CONSTRAINT fk_enrollments_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        CONSTRAINT fk_enrollments_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # learning_records
    op.execute("""
    CREATE TABLE learning_records (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        course_id BIGINT UNSIGNED NOT NULL,
        courseware_id BIGINT UNSIGNED NOT NULL,
        last_position INT UNSIGNED NOT NULL DEFAULT 0,
        progress_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
        duration_watched INT UNSIGNED NOT NULL DEFAULT 0,
        is_completed TINYINT(1) NOT NULL DEFAULT 0,
        last_learned_at DATETIME NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_lr_user_courseware (user_id, courseware_id),
        KEY idx_lr_user_course (user_id, course_id),
        CONSTRAINT fk_lr_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        CONSTRAINT fk_lr_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_lr_courseware FOREIGN KEY (courseware_id) REFERENCES courseware (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # notes
    op.execute("""
    CREATE TABLE notes (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        course_id BIGINT UNSIGNED NOT NULL,
        chapter_id BIGINT UNSIGNED NULL,
        courseware_id BIGINT UNSIGNED NULL,
        content TEXT NOT NULL,
        video_timestamp INT UNSIGNED NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_notes_user_id (user_id),
        KEY idx_notes_courseware_id (courseware_id),
        CONSTRAINT fk_notes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        CONSTRAINT fk_notes_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_notes_chapter FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL,
        CONSTRAINT fk_notes_courseware FOREIGN KEY (courseware_id) REFERENCES courseware (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # favorites
    op.execute("""
    CREATE TABLE favorites (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        target_type ENUM('course','courseware','note') NOT NULL,
        target_id BIGINT UNSIGNED NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_favorites_user_target (user_id, target_type, target_id),
        KEY idx_favorites_target (target_type, target_id),
        CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # learning_calendar
    op.execute("""
    CREATE TABLE learning_calendar (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        study_date DATE NOT NULL,
        duration_seconds INT UNSIGNED NOT NULL DEFAULT 0,
        courseware_count INT UNSIGNED NOT NULL DEFAULT 0,
        note_count INT UNSIGNED NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_lc_user_date (user_id, study_date),
        KEY idx_lc_study_date (study_date),
        CONSTRAINT fk_lc_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # knowledge_points
    op.execute("""
    CREATE TABLE knowledge_points (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id BIGINT UNSIGNED NOT NULL,
        parent_id BIGINT UNSIGNED NULL,
        name VARCHAR(128) NOT NULL,
        description TEXT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_kp_course_id (course_id),
        KEY idx_kp_parent_id (parent_id),
        CONSTRAINT fk_kp_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_kp_parent FOREIGN KEY (parent_id) REFERENCES knowledge_points (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # questions
    op.execute("""
    CREATE TABLE questions (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id BIGINT UNSIGNED NOT NULL,
        type ENUM('single','multiple','judge','short_answer') NOT NULL,
        stem TEXT NOT NULL,
        options JSON NULL,
        answer JSON NOT NULL,
        analysis TEXT NULL,
        difficulty TINYINT NOT NULL DEFAULT 3,
        score INT NOT NULL DEFAULT 5,
        created_by BIGINT UNSIGNED NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_questions_course_id (course_id),
        KEY idx_questions_type (type),
        KEY idx_questions_created_by (created_by),
        CONSTRAINT fk_questions_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_questions_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # question_knowledge_points
    op.execute("""
    CREATE TABLE question_knowledge_points (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        question_id BIGINT UNSIGNED NOT NULL,
        knowledge_point_id BIGINT UNSIGNED NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uk_qkp (question_id, knowledge_point_id),
        KEY idx_qkp_knowledge_point_id (knowledge_point_id),
        CONSTRAINT fk_qkp_question FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE,
        CONSTRAINT fk_qkp_knowledge_point FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # exams
    op.execute("""
    CREATE TABLE exams (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id BIGINT UNSIGNED NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT NULL,
        duration_minutes INT UNSIGNED NOT NULL,
        total_score INT UNSIGNED NOT NULL DEFAULT 100,
        pass_score INT UNSIGNED NOT NULL DEFAULT 60,
        start_time DATETIME NULL,
        end_time DATETIME NULL,
        status ENUM('draft','published','closed') NOT NULL DEFAULT 'draft',
        created_by BIGINT UNSIGNED NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_exams_course_id (course_id),
        KEY idx_exams_status (status),
        KEY idx_exams_created_by (created_by),
        CONSTRAINT fk_exams_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        CONSTRAINT fk_exams_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # exam_questions
    op.execute("""
    CREATE TABLE exam_questions (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        exam_id BIGINT UNSIGNED NOT NULL,
        question_id BIGINT UNSIGNED NOT NULL,
        score INT NOT NULL,
        sort_order INT NOT NULL DEFAULT 0,
        PRIMARY KEY (id),
        UNIQUE KEY uk_exam_questions (exam_id, question_id),
        KEY idx_eq_question_id (question_id),
        CONSTRAINT fk_eq_exam FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE,
        CONSTRAINT fk_eq_question FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # exam_records
    op.execute("""
    CREATE TABLE exam_records (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        exam_id BIGINT UNSIGNED NOT NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        answers JSON NULL,
        score DECIMAL(6,2) NULL,
        status ENUM('in_progress','submitted','graded') NOT NULL DEFAULT 'in_progress',
        started_at DATETIME NULL,
        submitted_at DATETIME NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_er_exam_user (exam_id, user_id),
        KEY idx_er_user_id (user_id),
        CONSTRAINT fk_er_exam FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE,
        CONSTRAINT fk_er_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # wrong_questions
    op.execute("""
    CREATE TABLE wrong_questions (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        question_id BIGINT UNSIGNED NOT NULL,
        exam_record_id BIGINT UNSIGNED NULL,
        wrong_answer JSON NULL,
        wrong_count INT UNSIGNED NOT NULL DEFAULT 1,
        is_mastered TINYINT(1) NOT NULL DEFAULT 0,
        last_wrong_at DATETIME NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_wq_user_question (user_id, question_id),
        KEY idx_wq_user_id (user_id),
        CONSTRAINT fk_wq_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        CONSTRAINT fk_wq_question FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE,
        CONSTRAINT fk_wq_exam_record FOREIGN KEY (exam_record_id) REFERENCES exam_records (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")

    # qa_history
    op.execute("""
    CREATE TABLE qa_history (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        course_id BIGINT UNSIGNED NULL,
        question TEXT NOT NULL,
        answer MEDIUMTEXT NULL,
        sources JSON NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY idx_qa_user_id (user_id),
        KEY idx_qa_course_id (course_id),
        CONSTRAINT fk_qa_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        CONSTRAINT fk_qa_course FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `qa_history`")
    op.execute("DROP TABLE IF EXISTS `wrong_questions`")
    op.execute("DROP TABLE IF EXISTS `exam_records`")
    op.execute("DROP TABLE IF EXISTS `exam_questions`")
    op.execute("DROP TABLE IF EXISTS `exams`")
    op.execute("DROP TABLE IF EXISTS `question_knowledge_points`")
    op.execute("DROP TABLE IF EXISTS `questions`")
    op.execute("DROP TABLE IF EXISTS `knowledge_points`")
    op.execute("DROP TABLE IF EXISTS `learning_calendar`")
    op.execute("DROP TABLE IF EXISTS `favorites`")
    op.execute("DROP TABLE IF EXISTS `notes`")
    op.execute("DROP TABLE IF EXISTS `learning_records`")
    op.execute("DROP TABLE IF EXISTS `enrollments`")
    op.execute("DROP TABLE IF EXISTS `courseware`")
    op.execute("DROP TABLE IF EXISTS `chapters`")
    op.execute("DROP TABLE IF EXISTS `courses`")
    op.execute("DROP TABLE IF EXISTS `categories`")
    op.execute("DROP TABLE IF EXISTS `users`")
