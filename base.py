import sys
import pymysql


class Base:
	def __init__(self, base_name, user, password, host):
		try:
			self.con = pymysql.connect(
				host=host,
				port=3306,
				user=user,
				password=password,
				database=base_name,
				max_allowed_packet=512 * 1024 * 1024,
				connect_timeout=10000,
				read_timeout=10000,
				write_timeout=10000
			)
		except Exception as error:
			print(error)
			sys.exit()
		self.create_tables()
		print('connect success!')

	def create_tables(self):
		tables = [
			'users(id integer primary key auto_increment, vk_id integer, mode varchar(100))',
			'notes(id integer primary key auto_increment, user_id integer, day varchar(50), body text)'
		]
		with self.con.cursor() as cur:
			for table in tables:
				cur.execute(
					f'create table if not exists {table};'
				)

	def get_user(self, vk_id):
		with self.con.cursor() as cur:
			cur.execute(f'SELECT * FROM users WHERE vk_id={vk_id};')
			if len([x for x in cur.fetchall()]) == 0:
				cur.execute(f'INSERT INTO users(vk_id, mode) VALUES({vk_id}, "start");')
				self.con.commit()
			cur.execute(f'SELECT * FROM users WHERE vk_id={vk_id};')
			return [{
				'id': x[0],
				'vk_id': x[1],
				'mode': x[2],
			} for x in cur.fetchall()][0]

	def add_note(self, user_id, note_body, day):
		with self.con.cursor() as cur:
			cur.execute(f'insert into notes(user_id, day, body) values({user_id}, "{day}", "{note_body}");')

	def get_user_notes(self, vk_id, day):
		with self.con.cursor() as cur:
			cur.execute(f'select * from notes where user_id={vk_id} and day="{day}"')
			return [{
				'id': x[0],
				'user_id': x[1],
				'day': x[2],
				'body': x[3]
			} for x in cur.fetchall()]

	def set_mode(self, vk_id, mode):
		with self.con.cursor() as cur:
			cur.execute(f'update users set mode="{mode}" where vk_id={vk_id};')
		self.con.commit()

	def del_note(self, note_id):
		with self.con.cursor() as cur:
			cur.execute(f'delete from notes where id={note_id};')

	def clear_user_notes(self, user_id):
		with self.con.cursor() as cur:
			cur.execute(f'delete from notes where user_id={user_id};')
