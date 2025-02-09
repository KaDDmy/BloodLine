import pygame
import random
import os
import sys
import math
import time

pygame.init()

# Константы
WIDTH, HEIGHT = 1280, 720
FPS = 60
PLAYER_SPEED = 5
ENEMY_SPEED = 3
BULLET_SPEED = 10
GUN_BULLET_SPEED = 7
PLAYER_SHOOT_INTERVAL = 300

GUN_SHOOT_INTERVAL = 1750  # Время между выстрелами в миллисекундах для GunEnemy()

RIFLE_SHOOT_INTERVAL = 2000  # Время между очередями в миллисекундах для RifleEnemy()
RIFLE_BURST_INTERVAL = 100  # Время между выстрелами в миллисекундах в очереди для RifleEnemy()
RIFLE_BULLET_COUNT = 8  # Количество пуль в 1 очереди у RifleEnemy()

MULTIPLIER_RESET_TIME = 650

# Цвета для теста(Потом будут спрайты)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class Level:
    def __init__(self):
        super().__init__()

    def show_new_level_screen(self, level_score):
        font = pygame.font.Font(None, 74)
        text = font.render(f"Level {self.levels[self.current_level_index]['level']}", True, WHITE)
        score_text = font.render(f"Level Score: {level_score}", True, WHITE)
        countdown_font = pygame.font.Font(None, 50)

        self.start_time = pygame.time.get_ticks()
        duration = 5000

        while True:
            elapsed_time = pygame.time.get_ticks() - self.start_time
            self.screen.fill(BLACK)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))
            self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 50))
            countdown_text = countdown_font.render(f"Starting in {5 - elapsed_time // 1000}...", True, WHITE)
            self.screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()

            if elapsed_time >= duration:
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

        Game.reset_game(self)


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, dx, dy):
        super().__init__()
        original_image = random.choice(game.particles_images)
        self.image = original_image.copy()
        self.rect = self.image.get_rect()

        self.velocity = [dx, dy]
        self.rect.center = pos

        self.alpha = 255

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # Замедление частиц
        self.velocity[0] *= 0.9
        self.velocity[1] *= 0.9

        self.alpha -= 2
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)  # Изменение прозрачности


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.original_image = Game.load_image('player-gun.png')
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)  # Маска
        self.last_shot_time = pygame.time.get_ticks()

    def move(self, keys):
        if keys["up"]:
            self.rect.y -= PLAYER_SPEED
        if keys["down"]:
            self.rect.y += PLAYER_SPEED
        if keys["left"]:
            self.rect.x -= PLAYER_SPEED
        if keys["right"]:
            self.rect.x += PLAYER_SPEED

        # Ограничение игрока внутри экрана
        self.rect.x = max(40, min(WIDTH - self.rect.width - 40, self.rect.x))
        self.rect.y = max(40, min(HEIGHT - self.rect.height - 40, self.rect.y))

    def look_at_cursor(self):
        """Поворачивает игрока в сторону курсора"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery

        angle = math.degrees(math.atan2(-dy, dx))  # Угол от врага к игроку

        # Поворот изображения
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def can_shoot(self):
        """Проверка возможности выстрела"""
        return (pygame.time.get_ticks() - self.last_shot_time) >= PLAYER_SHOOT_INTERVAL

    def shoot(self, mouse_pos):
        # Сброс таймера выстрела
        self.last_shot_time = pygame.time.get_ticks()

        # Координаты курсора мыши
        mouse_x, mouse_y = pygame.mouse.get_pos()
        bullet = Bullet(self.rect.centerx, self.rect.centery)

        # Направление пули к курсору
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        dist = max((dx ** 2 + dy ** 2) ** 0.5, 1)
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        bullet.vx = (dx / dist) * BULLET_SPEED
        bullet.vy = (dy / dist) * BULLET_SPEED
        return bullet

    def update(self, keys):
        self.move(keys)
        self.look_at_cursor()


class EnemyBase(pygame.sprite.Sprite):
    def __init__(self, x, y, image, dead_image):
        super().__init__()
        self.is_dead = False
        self.dead_image = dead_image
        self.original_image = Game.load_image(image)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)  # Маска

    def look_at_player(self, player):
        """Поворачивает врага на игроку"""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        self.current_angle = math.degrees(math.atan2(-dy, dx))  # Угол от врага к игроку

        # Поворот изображения
        self.image = pygame.transform.rotate(self.original_image, self.current_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def die(self):
        """Убивает врага - меняет спрайт и удаляет маску"""
        self.is_dead = True
        Game.create_particles(game, (self.rect.centerx, self.rect.centery))
        dead_image = Game.load_image(self.dead_image)
        self.image = pygame.transform.rotate(dead_image, self.current_angle)
        self.mask = None


class Enemy(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, 'enemy-knife.png',
                         f'enemy-knife-dead-type{random.randint(1, 4)}.png')

    def move_towards(self, target):
        if target.x > self.rect.x:
            self.rect.x += ENEMY_SPEED
        if target.x < self.rect.x:
            self.rect.x -= ENEMY_SPEED
        if target.y > self.rect.y:
            self.rect.y += ENEMY_SPEED
        if target.y < self.rect.y:
            self.rect.y -= ENEMY_SPEED

    def update(self, player):
        self.look_at_player(player)


class GunEnemy(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, 'enemy-gun.png',
                         f'enemy-gun-dead-type{random.randint(1, 4)}.png')
        self.last_shot_time = pygame.time.get_ticks()

    def shoot(self, target):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= GUN_SHOOT_INTERVAL:
            self.last_shot_time = current_time
            bullet = Bullet(self.rect.centerx, self.rect.centery)
            # Направление к игроку
            dx = target.centerx - self.rect.centerx
            dy = target.centery - self.rect.centery
            dist = max((dx ** 2 + dy ** 2) ** 0.5, 1)
            bullet.vx = (dx / dist) * GUN_BULLET_SPEED
            bullet.vy = (dy / dist) * GUN_BULLET_SPEED

            return bullet
        return None

    def update(self, player):
        self.look_at_player(player)


class RifleEnemy(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, 'enemy-rifle.png',
                         f'enemy-rifle-dead-type{random.randint(1, 4)}.png')
        self.bullet_counter = 0
        self.last_shot_time = pygame.time.get_ticks()  # Последний выстрел
        self.next_burst_time = pygame.time.get_ticks() + RIFLE_SHOOT_INTERVAL  # Время для начала новой очереди

    def shoot(self, target):
        current_time = pygame.time.get_ticks()

        # Ожидание новой очереди
        if self.bullet_counter == 0 and current_time < self.next_burst_time:
            return None

        # Начало новой очереди
        if self.bullet_counter == 0 and current_time >= self.next_burst_time:
            self.bullet_counter = RIFLE_BULLET_COUNT

        # Стрельба очереди
        if self.bullet_counter > 0 and current_time - self.last_shot_time >= RIFLE_BURST_INTERVAL:
            self.last_shot_time = current_time
            self.bullet_counter -= 1

            bullet = Bullet(self.rect.centerx, self.rect.centery, bullet_image='bullet5x5.png')
            # Направление к игроку
            dx = target.centerx - self.rect.centerx
            dy = target.centery - self.rect.centery
            dist = max((dx ** 2 + dy ** 2) ** 0.5, 1)
            bullet.vx = (dx / dist) * GUN_BULLET_SPEED
            bullet.vy = (dy / dist) * GUN_BULLET_SPEED

            if self.bullet_counter == 0:
                self.next_burst_time = current_time + RIFLE_SHOOT_INTERVAL

            return bullet
        return None

    def update(self, player):
        self.look_at_player(player)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, bullet_image='bullet7x7.png'):
        super().__init__()
        self.image = Game.load_image(bullet_image)
        self.rect = self.image.get_rect(center=(x, y))

        self.x, self.y = float(x), float(y)

        self.vx = 0
        self.vy = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy

        self.rect.center = (int(self.x), int(self.y))

        # Удаление пули, если она за экраном
        if self.rect.y < 42 or self.rect.y > HEIGHT - 42 or self.rect.x < 42 or self.rect.x > WIDTH - 42:
            self.kill()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BloodLine")
        self.bloodline_icon = Game.load_image('BloodLineLogoNoBG.png')
        pygame.display.set_icon(self.bloodline_icon)
        self.clock = pygame.time.Clock()
        self.running = True
        self.green_intensity = 255
        self.fade_speed = 1
        self.current_level_index = 0
        self.current_level = None
        self.text = [
            "> Mission - BLOODLINE",
            ">",
            "> Objective - defeat an underground cartel, involved in the",
            "> creation and distribution of a deadly drug called \"Bloodline\"",
            ">",
            "> Location - USA, Albuquerque, abandoned warehouse",
            ">",
            "> Time - 11:00 p.m."
        ]
        self.line_spacing = 40
        self.delay_per_char = 60  # Задержка между символами в миллисекундах
        self.start_x, self.start_y = 20, 20

        # Переменные для отслеживания состояния
        self.current_line = 0
        self.current_char = 0
        self.last_update_time = pygame.time.get_ticks()  # Время последнего обновления
        self.rendered_lines = []
        self.font = pygame.font.Font(None, 36)

        self.background_image = Game.load_image('background.png').convert()
        self.hit_sounds = ["hit_3.mp3", "hit_2.mp3", "hit_4.mp3", "hit_5.mp3", "hit_6.mp3"]
        self.player_hit = pygame.mixer.Sound("data/sounds/player_death.mp3")
        self.player_hit.set_volume(0.65)
        # self.enemy_rifle_sound.play() - звук выстрела противника с пулеметом
        # self.enemy_shot_sound.play() - звук выстрела противника с пистолетом
        self.enemy_rifle_sound = pygame.mixer.Sound("data/sounds/thompson.mp3")
        self.enemy_rifle_sound.set_volume(0.3)
        self.enemy_shot_sound = pygame.mixer.Sound("data/sounds/enemy_shot.mp3")
        self.enemy_shot_sound.set_volume(0.3)
        self.shot_sound = pygame.mixer.Sound("data/sounds/shot.mp3")
        self.shot_sound.set_volume(0.3)
        self.background_tracks = ["Sleepless-City.mp3", "Ghostrifter.mp3", "NeonDrive.mp3"]  # Список MP3-файлов
        self.current_track_index = random.randint(0, len(self.background_tracks) - 1)  # Выбор случайного трека
        pygame.mixer.music.set_volume(0.3)
        self.menu_tracks = 'IntoTheWilds.mp3'
        self.game_state = 'menu'

        # Система очков
        self.score = 0
        self.total_score = 0
        self.multiplier = 1.0
        self.multiplier_reset_time = 0

        # Курсор в виде прицела
        pygame.mouse.set_visible(False)
        self.cursor_sprite = pygame.sprite.Sprite()
        self.cursor_sprite.image = Game.load_image("cursor.png")
        self.cursor_sprite.rect = self.cursor_sprite.image.get_rect()
        self.cursor_group = pygame.sprite.GroupSingle(self.cursor_sprite)

        # Прелоад партиклов
        self.preload_particles()

        # Уровни
        self.levels = [
            {"level": 0, "knife_enemies": 2, "gun_enemies": 0, "rifle_enemies": 0},
            {"level": 1, "knife_enemies": 2, "gun_enemies": 1, "rifle_enemies": 0},
            {"level": 2, "knife_enemies": 1, "gun_enemies": 1, "rifle_enemies": 1},
            {"level": 3, "knife_enemies": 3, "gun_enemies": 2, "rifle_enemies": 1},
            {"level": 4, "knife_enemies": 3, "gun_enemies": 2, "rifle_enemies": 2},
            {"level": 5, "knife_enemies": 4, "gun_enemies": 4, "rifle_enemies": 2},
            {"level": 6, "knife_enemies": 4, "gun_enemies": 3, "rifle_enemies": 3},
            {"level": 7, "knife_enemies": 5, "gun_enemies": 4, "rifle_enemies": 3},
            {"level": 8, "knife_enemies": 5, "gun_enemies": 5, "rifle_enemies": 4},
        ]
        self.menu()

    def menu(self):
        self.current_level_index = 0
        self.current_level = None
        self.score = 0
        self.total_score = 0
        self.multiplier = 1.0
        self.multiplier_reset_time = 0
        self.current_line = 0
        self.current_char = 0
        self.last_update_time = pygame.time.get_ticks()  # Время последнего обновления
        self.rendered_lines = []
        self.font = pygame.font.Font(None, 36)
        image = pygame.image.load("data/images/menu.png")
        image_rect = image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        font = pygame.font.Font(None, 40)
        text_color = (89, 0, 0)
        shadow_color = (0, 0, 0)  # Темный цвет для тени
        blink_interval = 0.5  # Интервал мигания (в секундах)
        last_blink_time = time.time()
        show_text = True
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    self.running = False
                    pygame.mixer.music.stop()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        self.draw_text_with_effect(self.screen)
                        # self.reset_game()
                        # pygame.mixer.music.stop()
                        # self.game_state = 'game'
                        run = False
            self.screen.fill((0, 0, 0))
            self.screen.blit(image, image_rect)
            if not pygame.mixer.music.get_busy():  # Если музыка не играет
                self.music()

            # Управление миганием текста
            current_time = time.time()
            if current_time - last_blink_time > blink_interval:
                show_text = not show_text
                last_blink_time = current_time

            # Отображение текста
            if show_text:
                text_surface = font.render("Нажмите ENTER, чтобы начать игру", True, text_color)
                shadow_surface = font.render("Нажмите ENTER, чтобы начать игру", True, shadow_color)
                shadow_surface.set_alpha(176)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                shadow_rect = text_rect.copy()
                shadow_rect.x, shadow_rect.y = shadow_rect.x + 2, shadow_rect.y + 2
                self.screen.blit(shadow_surface, shadow_rect)
                self.screen.blit(text_surface, text_rect)
            pygame.display.flip()

    def draw_text_with_effect(self, screen):
        running = True
        font = pygame.font.Font(None, 36)
        text_color = (0, 200, 0)
        shadow_color = (0, 0, 0)  # Темный цвет для тени
        blink_interval = 0.5  # Интервал мигания (в секундах)
        last_blink_time = time.time()
        show_text = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.running = False
                    pygame.mixer.music.stop()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        self.reset_game()
                        pygame.mixer.music.stop()
                        self.game_state = 'game'
                        running = False
            screen.fill((0, 0, 0))  # Очистить экран

            # Получение текущего времени
            now = pygame.time.get_ticks()

            # Логика печати текста
            if self.current_line < len(self.text):
                if now - self.last_update_time > self.delay_per_char:
                    self.last_update_time = now  # Обновить время последнего изменения

                    # Добавить следующий символ к текущей строке
                    if self.current_char < len(self.text[self.current_line]):
                        self.current_char += 1
                    else:
                        # Переход к следующей строке
                        self.rendered_lines.append(self.text[self.current_line])
                        self.current_line += 1
                        self.current_char = 0
            else:
                self.reset_game()
                pygame.mixer.music.stop()
                self.game_state = 'game'
                running = False

            # Отрисовка текста
            for i, line in enumerate(self.rendered_lines):
                text_surface = self.font.render(line, True, (0, 255, 0))
                screen.blit(text_surface, (self.start_x, self.start_y + i * self.line_spacing))

            # Отрисовка текущей печатающейся строки
            if self.current_line < len(self.text):
                current_text = self.text[self.current_line][:self.current_char]
                text_surface = self.font.render(current_text, True, GREEN)
                screen.blit(text_surface, (self.start_x, self.start_y + self.current_line * self.line_spacing))

            current_time = time.time()
            if current_time - last_blink_time > blink_interval:
                show_text = not show_text
                last_blink_time = current_time

            # Отображение текста
            if show_text:
                text_surface = font.render("Нажмите ENTER, чтобы пропустить", True, text_color)
                shadow_surface = font.render("Нажмите ENTER, чтобы пропустить", True, shadow_color)
                shadow_surface.set_alpha(176)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                shadow_rect = text_rect.copy()
                shadow_rect.x, shadow_rect.y = shadow_rect.x + 2, shadow_rect.y + 2
                self.screen.blit(shadow_surface, shadow_rect)
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()

    def music(self):
        if self.game_state == 'game':
            if self.current_track_index < len(self.background_tracks):
                pygame.mixer.music.load(f'data/sounds/{self.background_tracks[self.current_track_index]}')
                pygame.mixer.music.play()
                self.current_track_index += 1
            else:
                self.current_track_index = 0  # Зациклить список
                self.music()
        elif self.game_state == 'menu':
            pygame.mixer.music.load(f'data/sounds/menu/{self.menu_tracks}')
            pygame.mixer.music.play()

    def hit(self):
        self.random_sound = random.choice(self.hit_sounds)
        self.hit_sound = pygame.mixer.Sound(f'data/sounds/{self.random_sound}')
        self.hit_sound.set_volume(0.2)
        self.hit_sound.play()

    def add_score(self, base_score):
        self.score += int(base_score * self.multiplier)
        self.multiplier = min(self.multiplier + 0.1, 2.0)
        self.multiplier_reset_time = pygame.time.get_ticks() + MULTIPLIER_RESET_TIME

    def update_multiplier(self):
        if pygame.time.get_ticks() > self.multiplier_reset_time:
            self.multiplier = max(self.multiplier - 0.1, 1.0)
            self.multiplier_reset_time = pygame.time.get_ticks() + MULTIPLIER_RESET_TIME

    def get_valid_spawn_pos(self, min_distance_from_player):
        """Генерирует корректные координаты спавна"""
        while True:
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)

            player_x, player_y = self.player.rect.center

            if (x - player_x) ** 2 + (y - player_y) ** 2 >= min_distance_from_player ** 2:
                return x, y

    def spawn_enemy(self, enemy, group, min_distance_from_player):
        x, y = self.get_valid_spawn_pos(min_distance_from_player)
        enemy_to_spawn = enemy(x, y)
        group.add(enemy_to_spawn)

    def preload_particles(self):
        self.particles_images = [pygame.transform.scale(image, (random.randint(75, 100),
                                                                random.randint(75, 100)))
                                 for image in (
                                     # Список партиклов
                                     Game.load_image('blood-particle-type1.png'),
                                     Game.load_image('blood-particle-type2.png'),
                                     Game.load_image('blood-particle-type3.png'),
                                     Game.load_image('blood-particle-type4.png'))
                                 for _ in range(5)]

    def create_particles(self, pos):
        """Создание частиц при смерти врага"""

        for _ in range(10):  # Количество частиц
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            particle = Particle(pos, dx, dy)
            self.particles_group.add(particle)

    def reset_game(self):
        """Создаёт/пересоздаёт все игровые объекты с нуля."""
        self.current_level = self.levels[self.current_level_index]  # Выбираем текущий уровень

        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.keys = {"up": False, "down": False, "left": False, "right": False}

        # Группы спрайтов
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.enemy_group = pygame.sprite.Group()
        self.gun_enemy_group = pygame.sprite.Group()
        self.rifle_enemy_group = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.dead_enemy_group = pygame.sprite.Group()
        self.particles_group = pygame.sprite.Group()

        # Создание врагов
        for _ in range(self.current_level["knife_enemies"]):
            self.spawn_enemy(Enemy, self.enemy_group, 175)

        for _ in range(self.current_level["gun_enemies"]):
            self.spawn_enemy(GunEnemy, self.gun_enemy_group, 325)

        for _ in range(self.current_level["rifle_enemies"]):
            self.spawn_enemy(RifleEnemy, self.rifle_enemy_group, 275)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.mixer.music.stop()

            if event.type == pygame.MOUSEMOTION:
                self.cursor_sprite.rect.center = event.pos

            if self.game_state == 'game':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.keys["up"] = True
                    if event.key == pygame.K_s:
                        self.keys["down"] = True
                    if event.key == pygame.K_a:
                        self.keys["left"] = True
                    if event.key == pygame.K_d:
                        self.keys["right"] = True
                    if event.key == pygame.K_t:
                        if self.current_track_index < len(self.background_tracks):
                            self.music()
                        else:
                            self.current_track_index = 0  # Зациклить список
                            self.music()
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                        self.music()
                        self.menu()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_w:
                        self.keys["up"] = False
                    if event.key == pygame.K_s:
                        self.keys["down"] = False
                    if event.key == pygame.K_a:
                        self.keys["left"] = False
                    if event.key == pygame.K_d:
                        self.keys["right"] = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка мыши
                        if self.player.can_shoot():
                            bullet = self.player.shoot(pygame.mouse.get_pos())
                            self.player_bullets.add(bullet)
                            self.shot_sound.play(maxtime=1000)


            elif self.game_state == 'game_over':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Перезапуск игры
                        self.reset_game()
                        self.game_state = "game"

                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                        self.music()
                        self.menu()

            elif self.game_state == 'win':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Перезапуск игры
                        self.green_intensity = 255
                        self.current_level_index = 0
                        self.multiplier = 1.0
                        self.total_score = 0
                        self.score = 0
                        self.reset_game()
                        self.game_state = "game"

                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                        self.music()
                        self.menu()

    def update(self):
        if self.game_state == 'game':
            # Движение игрока
            self.player.update(self.keys)

            # Обновление частиц
            self.particles_group.update()

            # Уменьшение множителя
            self.update_multiplier()

            # Обновление врагов
            self.gun_enemy_group.update(self.player)
            self.enemy_group.update(self.player)
            self.rifle_enemy_group.update(self.player)

            # Движение врагов к игроку
            for enemy in self.enemy_group:
                enemy.move_towards(self.player.rect)

            # Стрельба врагов
            for gun_enemy in self.gun_enemy_group:
                bullet = gun_enemy.shoot(self.player.rect)
                if bullet:
                    self.enemy_bullets.add(bullet)

            for rifle_enemy in self.rifle_enemy_group:
                bullet = rifle_enemy.shoot(self.player.rect)
                if bullet:
                    self.enemy_bullets.add(bullet)

            if not pygame.mixer.music.get_busy():  # Если музыка не играет
                self.music()

            # Обновление пуль
            self.player_bullets.update()
            self.enemy_bullets.update()

            self.check_mask_collisions()

    def check_mask_collisions(self):
        player_hit_by_enemy = pygame.sprite.spritecollide(self.player, self.enemy_group, False,
                                                          collided=pygame.sprite.collide_mask)
        player_hit_by_gun_enemy = pygame.sprite.spritecollide(self.player, self.gun_enemy_group, False,
                                                              collided=pygame.sprite.collide_mask)

        bullet_hits_player = pygame.sprite.spritecollide(
            self.player, self.enemy_bullets, True, collided=pygame.sprite.collide_mask)

        if bullet_hits_player or player_hit_by_enemy or player_hit_by_gun_enemy:
            self.score = 0
            self.multiplier = 1.0
            self.player_hit.play()
            self.game_over()

        bullets_hit_enemies = pygame.sprite.groupcollide(
            self.player_bullets, self.enemy_group, True, False, collided=pygame.sprite.collide_mask)
        for bullet, enemies in bullets_hit_enemies.items():
            for enemy in enemies:
                enemy.die()
                self.hit()
                self.enemy_group.remove(enemy)
                self.dead_enemy_group.add(enemy)
                self.add_score(750)

        bullets_hit_gun_enemies = pygame.sprite.groupcollide(
            self.player_bullets, self.gun_enemy_group, True, False, collided=pygame.sprite.collide_mask)
        for bullet, enemies in bullets_hit_gun_enemies.items():
            for enemy in enemies:
                enemy.die()
                self.hit()
                self.gun_enemy_group.remove(enemy)
                self.dead_enemy_group.add(enemy)
                self.add_score(1000)

        bullets_hit_rifle_enemies = pygame.sprite.groupcollide(
            self.player_bullets, self.rifle_enemy_group, True, False, collided=pygame.sprite.collide_mask)
        for bullet, enemies in bullets_hit_rifle_enemies.items():
            for enemy in enemies:
                enemy.die()
                self.hit()
                self.rifle_enemy_group.remove(enemy)
                self.dead_enemy_group.add(enemy)
                self.add_score(1250)

        if sum([len(self.enemy_group), len(self.gun_enemy_group), len(self.rifle_enemy_group)]) == 0:
            self.total_score += self.score
            self.current_level_index += 1
            if self.current_level_index < len(self.levels):
                Level.show_new_level_screen(self, self.score)
                self.score = 0
                self.multiplier = 1.0
            else:
                self.game_state = 'win'
                pygame.mixer.music.stop()

    def draw(self):
        if self.game_state == 'game':
            self.screen.blit(self.background_image, (0, 0))

            # Отрисовка групп
            self.particles_group.draw(self.screen)
            self.dead_enemy_group.draw(self.screen)

            self.enemy_group.draw(self.screen)
            self.gun_enemy_group.draw(self.screen)
            self.rifle_enemy_group.draw(self.screen)
            self.player_bullets.draw(self.screen)
            self.enemy_bullets.draw(self.screen)

            self.player_group.draw(self.screen)

            # Отрисовка системы очков
            font = pygame.font.SysFont(None, 40)
            # Тень
            score_text_shadow = font.render(f"Score: {self.score}", True, BLACK)
            multiplier_text_shadow = font.render(f"Multiplier: x{self.multiplier:.1f}", True, BLACK)
            score_text_shadow.set_alpha(176)
            multiplier_text_shadow.set_alpha(176)
            self.screen.blit(score_text_shadow, (12, 12))
            self.screen.blit(multiplier_text_shadow, (12, 52))
            # Текст
            score_text = font.render(f"Score: {self.score}", True, WHITE)
            multiplier_text = font.render(f"Multiplier: x{self.multiplier:.1f}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(multiplier_text, (10, 50))

            # Отрисовка курсора
            if pygame.mouse.get_focused():
                self.cursor_group.draw(self.screen)

            if self.current_level_index == 0:
                font_small1 = pygame.font.SysFont(None, 30)
                instruction_text = font_small1.render("[Controls: Moving - WASD, Shooting - LMB]", True, WHITE)
                instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                instruction_text.set_alpha(150)
                self.screen.blit(instruction_text, instruction_rect)
            if self.current_level_index == 1:
                font_small2 = pygame.font.SysFont(None, 30)
                instruction2_text = font_small2.render("[Controls: Change music - T]", True, WHITE)
                instruction2_rect = instruction2_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                instruction2_text.set_alpha(150)
                self.screen.blit(instruction2_text, instruction2_rect)

        elif self.game_state == 'game_over':
            # Рисуем экран Game Over
            self.screen.fill((30, 0, 0))  # Тёмно-красный фон
            font = pygame.font.SysFont(None, 100)
            text = font.render("GAME OVER", True, (255, 50, 50))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)

            font_small = pygame.font.SysFont(None, 60)
            restart_text = font_small.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)

            font_instr3 = pygame.font.SysFont(None, 30)
            instruction3_text = font_instr3.render("[Controls: Back to menu - Esc]", True, WHITE)
            instruction3_rect = instruction3_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
            instruction3_text.set_alpha(150)
            self.screen.blit(instruction3_text, instruction3_rect)

        elif self.game_state == 'win':
            if self.green_intensity > 0:
                self.green_intensity -= self.fade_speed

            # Заполнение экрана текущим зеленым цветом
            self.screen.fill((0, self.green_intensity, 0))

            # Отображение текста
            font = pygame.font.SysFont(None, 100)
            text = font.render("YOU WIN!", True, (204, 204, 51))
            score_text = font.render(f"Total Score: {self.total_score}", True, (204, 204, 51))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)
            self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 50))

            font_small = pygame.font.SysFont(None, 60)
            restart_text = font_small.render("Press 'Enter' to Play Again", True, (204, 204, 51))
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def load_image(name, colorkey=None):
        """Загрузка изображений"""
        fullname = os.path.join('data/images', name)
        if not os.path.isfile(fullname):
            print(f"Файл с изображением '{fullname}' не найден")
            sys.exit()
        image = pygame.image.load(fullname)
        return image

    def game_over(self):
        self.game_state = 'game_over'

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
