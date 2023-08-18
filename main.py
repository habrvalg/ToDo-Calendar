import sys
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import json
from base import Base
import utils


class MyLongPoll(VkLongPoll):
	def listen(self):
		while True:
			try:
				for event in self.check():
					yield event
			except Exception as error:
				print(error)


class Bot:
	def __init__(self):
		self.conf = {}
		self.load_config()
		self.base = Base(self.conf['db_name'], self.conf['db_user'], self.conf['db_password'], self.conf['host'])

		self.vk_session = vk_api.VkApi(token=self.conf['token'])
		self.longpoll = MyLongPoll(self.vk_session)
		self.menu_key = utils.get_keyboard([
			[('Понедельник', 'зеленый'), ('Вторник', 'зеленый')],
			[('Среда', 'зеленый'), ('Четверг', 'зеленый')],
			[('Пятница', 'зеленый'), ('Суббота', 'зеленый')],
			[('Воскресенье', 'зеленый')]
		])
		self.days_menu = utils.get_keyboard([
			[('Добавить заметку', 'зеленый'), ('Удалить заметку', 'красный')],
			[('Назад', 'синий')]
		])
		self.back_key = utils.get_keyboard([
			[('Назад', 'синий')]
		])

		self.days = {
			'понедельник': 'пн', 'вторник': 'вт',
			'среда': 'ср', 'четверг': 'чт',
			'пятница': 'пт', 'суббота': 'сб',
			'воскресенье': 'вс',
		}

	def load_config(self):
		with open('config.json', 'r') as file:
			self.conf = json.load(file)
		if len(self.conf) == 0:
			sys.exit()

	def sender(self, id, text, key=utils.get_keyboard([])):
		self.vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0, 'keyboard': key})

	def run(self):
		for event in self.longpoll.listen():
			if (event.type == VkEventType.MESSAGE_NEW) and event.to_me and not event.from_me:

				message = event.text
				msg = event.text.lower()
				user_id = event.user_id
				user = self.base.get_user(user_id)

				if msg == 'начать':
					self.base.set_mode(user_id, f'start')
					self.sender(user_id, 'Выберите день недели:', self.menu_key)

				elif msg == '/clear':
					self.base.clear_user_notes(user_id)
					self.sender(user_id, 'Вы очистили все свои заметки!', self.menu_key)
					self.base.set_mode(user_id, 'start')

				if user['mode'] == 'start':
					if msg in self.days:
						user_notes = self.base.get_user_notes(user_id, self.days[msg])
						ans = f'Ваши заметки на <{message}>:\n'
						if len(user_notes) == 0:
							ans = f'У вас нет заметок на <{message}>!'
						else:
							num = 1
							for note in user_notes:
								ans = f'{ans}\n{num}) {note["body"]}'
								num += 1
						self.sender(user_id, ans, self.days_menu)
						self.base.set_mode(user_id, f'notes_{self.days[msg]}')

				elif user['mode'].startswith('notes_') and user['mode'].replace('notes_', '') in [self.days[x] for x in self.days]:
					day = user['mode'].replace('notes_', '')
					"""     Режимы: notes_<>     """
					if msg == 'добавить заметку':
						self.sender(user_id, 'Введите текст заметки:', self.back_key)
						self.base.set_mode(user_id, f'append_note_{day}')

					elif msg == 'удалить заметку':
						user_notes = self.base.get_user_notes(user_id, day)
						ans = f'Введите номер заметки, которую хотите удалить:'
						if len(user_notes) == 0:
							ans = f'У вас нет заметок на <{day}>!'
						else:
							num = 1
							for note in user_notes:
								ans = f'{ans}\n{num}) {note["body"]}'
								num += 1
						self.sender(user_id, ans, self.back_key)
						self.base.set_mode(user_id, f'del_note_{day}')

					elif msg == 'назад':
						self.base.set_mode(user_id, 'start')
						self.sender(user_id, 'Выберите день недели:', self.menu_key)

				elif user['mode'].startswith('append_note_') and user['mode'].replace('append_note_', '') in [self.days[x] for x in self.days]:
					day = user['mode'].replace('append_note_', '')

					if msg == 'назад':
						user_notes = self.base.get_user_notes(user_id, day)
						ans = 'Ваши заметки:'
						if len(user_notes) == 0:
							ans = f'У вас нет заметок на <{day}>!'
						else:
							num = 1
							for note in user_notes:
								ans = f'{ans}\n{num}) {note["body"]}'
								num += 1
						self.sender(user_id, ans, self.days_menu)
						self.base.set_mode(user_id, f'notes_{day}')
					else:
						self.base.add_note(user_id, message, day)

						ans = 'Заметка добавлена!\n'
						user_notes = self.base.get_user_notes(user_id, day)
						num = 1
						for note in user_notes:
							ans = f'{ans}\n{num}) {note["body"]}'
							num += 1

						self.sender(user_id, ans, self.days_menu)
						self.base.set_mode(user_id, f'notes_{day}')

				elif user['mode'].startswith('del_note_') and user['mode'].replace('del_note_', '') in [self.days[x] for x in self.days]:
					day = user['mode'].replace('del_note_', '')

					if msg == 'назад':
						user_notes = self.base.get_user_notes(user_id, day)
						ans = 'Ваши заметки:'
						if len(user_notes) == 0:
							ans = f'У вас нет заметок на <{day}>!'
						else:
							num = 1
							for note in user_notes:
								ans = f'{ans}\n{num}) {note["body"]}'
								num += 1
						self.sender(user_id, ans, self.days_menu)
						self.base.set_mode(user_id, f'notes_{day}')

					elif msg.isdigit():
						user_notes = self.base.get_user_notes(user_id, day)
						if len(user_notes) >= int(msg) > 0:
							note_id = user_notes[int(msg)-1]['id']
							self.base.del_note(note_id)
							ans = 'Заметка удалена!\n\nВаши заметки:'
							num = 1
							for note in user_notes:
								if note['id'] != note_id:
									ans = f'{ans}\n{num}) {note["body"]}'
									num += 1
							self.sender(user_id, ans, self.days_menu)
							self.base.set_mode(user_id, f'notes_{day}')


if __name__ == '__main__':
	Bot().run()
