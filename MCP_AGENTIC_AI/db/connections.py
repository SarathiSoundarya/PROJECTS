import sqlite3


class SessionDB:
    def __init__(self, path="sessions.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init_tables()


    def _init_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chat_session_id TEXT NOT NULL,
            current INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            is_delete INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chat_session_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            question TEXT,
            answer TEXT,
            current INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            is_delete INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()
    
    def create_chat_session(self, user_id: int):

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT COALESCE(MAX(CAST(chat_session_id AS INTEGER)), 0) + 1
            FROM chat_sessions
            WHERE user_id = ?
        """, (user_id,))

        chat_session_id = cursor.fetchone()[0]
        print(f"Generated chat_session_id: {chat_session_id} for user_id: {user_id}")
        #mark old sessions as not current
        cursor.execute("""
            UPDATE chat_sessions
            SET current = 0
            WHERE user_id = ?
        """, (user_id,))

        #insert new session
        cursor.execute("""
            INSERT INTO chat_sessions (
                user_id,
                chat_session_id,
                current,
                active,
                is_delete,
                created_at
            )
            VALUES (?, ?, 1, 1, 0, CURRENT_TIMESTAMP)
        """, (
            user_id,
            chat_session_id
        ))

        self.conn.commit()

        return chat_session_id

    
    #create a new chat_id and insert the question
    def create_chat_id(self, user_id: int, chat_session_id: int, question: str) -> int:
        cursor = self.conn.cursor()

        #get next chat_id
        cursor.execute("""
            SELECT COALESCE(MAX(CAST(chat_id AS INTEGER)), 0) + 1
            FROM chats
            WHERE user_id = ? AND chat_session_id = ?
        """, (user_id, chat_session_id))

        chat_id = cursor.fetchone()[0]

        #insert question only
        cursor.execute("""
            INSERT INTO chats (
                user_id,
                chat_session_id,
                chat_id,
                question,
                current,
                active,
                is_delete,
                created_at
            )
            VALUES (?, ?, ?, ?, 1, 1, 0, CURRENT_TIMESTAMP)
        """, (
            user_id,
            chat_session_id,
            chat_id,
            question
        ))

        self.conn.commit()
        return chat_id

    #  Update the answer for an existing chat
    def update_chat_answer(self, user_id: int, chat_session_id: int, chat_id: int, answer: str):
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE chats
            SET answer = ?
            WHERE user_id = ? AND chat_session_id = ? AND chat_id = ?
        """, (answer, user_id, chat_session_id, chat_id))

        self.conn.commit()

   
    #get last n chats for a session
    def get_last_chats(
        self,
        chat_session_id: str,
        chat_id: str,
        limit: int = 5
    ):

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT question, answer
        FROM chats
        WHERE chat_session_id = ? AND chat_id != ?
        AND is_delete = 0
        ORDER BY id DESC
        LIMIT ?
        """, (chat_session_id, chat_id, limit))

        rows = cursor.fetchall()

        rows.reverse()

        return rows

    
    def delete_session(self, chat_session_id: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE chat_sessions
        SET is_delete = 1, active = 0, current = 0
        WHERE chat_session_id = ?
        """, (chat_session_id,))

        self.conn.commit()


    def delete_chat(self, chat_id: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE chats
        SET is_delete = 1, active = 0, current = 0
        WHERE chat_id = ?
        """, (chat_id,))

        self.conn.commit()
