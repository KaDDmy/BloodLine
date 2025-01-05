import pygame
import random
import os
import sys
import math

pygame.init()

# Константы
WIDTH, HEIGHT = 1280, 720
FPS = 60
PLAYER_SPEED = 5
ENEMY_SPEED = 3
BULLET_SPEED = 10
GUN_BULLET_SPEED = 7
PLAYER_SHOOT_INTERVAL = 0
GUN_SHOOT_INTERVAL = 2000  # Время между выстрелами в миллисекундах

# Цвета для теста(Потом будут спрайты)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class Level:
    pass


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
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
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

    def look_at_cursor(self):
        """Поворачивает игрока а сторону курсора"""
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
    def __init__(self, x, y, image):
        super().__init__()
        self.original_image = Game.load_image(image)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)  # Маска

    def look_at_player(self, player):
        """Поворачивает врага на игроку"""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        angle = math.degrees(math.atan2(-dy, dx))  # Угол от врага к игроку

        # Поворот изображения
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)


class Enemy(EnemyBase):
    def __init__(self, x, y):
        super().__init__(x, y, 'enemy-knife.png')

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
        super().__init__(x, y, 'enemy-gun.png')
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


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = Game.load_image('bullet7x7.png')
        self.rect = self.image.get_rect(center=(x, y))
        self.rect.center = (x, y)

        self.vx = 0
        self.vy = 0

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Удаление пули, если она за экраном
        if self.rect.y < 0 or self.rect.y > HEIGHT or self.rect.x < 0 or self.rect.x > WIDTH:
            self.kill()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BloodLine")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = 'game'
        self.reset_game()

    def reset_game(self):
        """Создаёт/пересоздаёт все игровые объекты с нуля."""
        self.player = Player(WIDTH // 2, HEIGHT // 2, 40, 40)
        self.keys = {"up": False, "down": False, "left": False, "right": False}

        # Группы спрайтов
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.enemy_group = pygame.sprite.Group()
        self.gun_enemy_group = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        # Создание врагов
        for _ in range(5):
            x = random.randint(0, WIDTH - 30)
            y = random.randint(0, HEIGHT - 30)
            enemy = Enemy(x, y)
            self.enemy_group.add(enemy)

        for _ in range(5):
            x = random.randint(0, WIDTH - 30)
            y = random.randint(0, HEIGHT - 30)
            gun_enemy = GunEnemy(x, y)
            self.gun_enemy_group.add(gun_enemy)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

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

            elif self.game_state == 'game_over':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Перезапуск игры
                        self.reset_game()
                        self.game_state = "game"

    def update(self):
        if self.game_state == 'game':
            # Движение игрока
            self.player.update(self.keys)

            # Обновление врагов
            self.gun_enemy_group.update(self.player)
            self.enemy_group.update(self.player)

            # Движение врагов к игроку
            for enemy in self.enemy_group:
                enemy.move_towards(self.player.rect)

            # Стрельба врагов
            for gun_enemy in self.gun_enemy_group:
                bullet = gun_enemy.shoot(self.player.rect)
                if bullet:
                    self.enemy_bullets.add(bullet)

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
            self.game_over()

        bullets_hit_enemies = pygame.sprite.groupcollide(
            self.player_bullets, self.enemy_group, True, True, collided=pygame.sprite.collide_mask)
        bullets_hit_gun_enemies = pygame.sprite.groupcollide(
            self.player_bullets, self.gun_enemy_group, True, True, collided=pygame.sprite.collide_mask)

    def draw(self):
        if self.game_state == 'game':
            self.screen.fill(BLACK)

            # Отрисовка групп
            self.player_group.draw(self.screen)
            self.enemy_group.draw(self.screen)
            self.gun_enemy_group.draw(self.screen)
            self.player_bullets.draw(self.screen)
            self.enemy_bullets.draw(self.screen)

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
