import pygame
import random

pygame.init()

# Константы
WIDTH, HEIGHT = 1280, 720
FPS = 60
PLAYER_SPEED = 5
ENEMY_SPEED = 2
BULLET_SPEED = 10
STATIC_BULLET_SPEED = 7
STATIC_SHOOT_INTERVAL = 3000  # Время между выстрелами в миллисекундах

# Цвета для теста(Потом будут спрайты)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class Level:
    pass


class Player:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

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

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, self.rect)


class Enemy:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def move_towards(self, target):
        if target.x > self.rect.x:
            self.rect.x += ENEMY_SPEED
        if target.x < self.rect.x:
            self.rect.x -= ENEMY_SPEED
        if target.y > self.rect.y:
            self.rect.y += ENEMY_SPEED
        if target.y < self.rect.y:
            self.rect.y -= ENEMY_SPEED

    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)


class StaticEnemy:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.last_shot_time = pygame.time.get_ticks()

    def shoot(self, bullets, target):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= STATIC_SHOOT_INTERVAL:
            self.last_shot_time = current_time
            bullet = Bullet(self.rect.centerx, self.rect.centery, 5, 5)
            # Направление к игроку
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = max((dx**2 + dy**2) ** 0.5, 1)
            bullet.vx = (dx / dist) * STATIC_BULLET_SPEED
            bullet.vy = (dy / dist) * STATIC_BULLET_SPEED
            bullets.append(bullet)

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)


class Bullet:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.vx = 0
        self.vy = 0

    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def is_off_screen(self):
        return self.rect.y < 0 or self.rect.y > HEIGHT or self.rect.x < 0 or self.rect.x > WIDTH

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BloodLine")
        self.clock = pygame.time.Clock()
        self.running = True

        # Игровые объекты
        self.player = Player(WIDTH // 2, HEIGHT // 2, 40, 40)
        self.enemies = [Enemy(random.randint(0, WIDTH - 15), random.randint(0, HEIGHT - 15), 30, 30) for _ in range(5)]
        self.static_enemies = [StaticEnemy(random.randint(0, WIDTH - 15), random.randint(0, HEIGHT - 15), 30, 30) for _ in range(3)]
        self.bullets = []
        self.enemy_bullets = []
        self.keys = {"up": False, "down": False, "left": False, "right": False}

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Обработка нажатий клавиш
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
                    self.shoot_bullet()

    def shoot_bullet(self):
        # Координаты курсора мыши
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Создаем пулю из центра игрока
        bullet = Bullet(self.player.rect.centerx, self.player.rect.centery, 5, 5)
        # Направление пули к курсору
        dx = mouse_x - self.player.rect.centerx
        dy = mouse_y - self.player.rect.centery
        dist = max((dx ** 2 + dy ** 2) ** 0.5, 1)
        bullet.vx = (dx / dist) * BULLET_SPEED
        bullet.vy = (dy / dist) * BULLET_SPEED
        self.bullets.append(bullet)

    def update(self):
        # Движение игрока
        self.player.move(self.keys)

        # Обновление пуль
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.is_off_screen():
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.is_off_screen():
                self.enemy_bullets.remove(bullet)

        # Движение врагов к игроку
        for enemy in self.enemies:
            enemy.move_towards(self.player.rect)

        # Стрельба статических врагов
        for static_enemy in self.static_enemies:
            static_enemy.shoot(self.enemy_bullets, self.player)

        # Проверка столкновений пуль с врагами
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    self.bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    break
            for enemy in self.static_enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    self.bullets.remove(bullet)
                    self.static_enemies.remove(enemy)
                    break

        # Проверка столкновений врагов с игроком
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                print("Game Over!")
                self.running = False

        # Проверка попадания статических пуль в игрока
        for bullet in self.enemy_bullets[:]:
            if bullet.rect.colliderect(self.player.rect):
                print("Game Over!")
                self.running = False

    def draw(self):
        self.screen.fill(BLACK)
        self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for static_enemy in self.static_enemies:
            static_enemy.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)

        pygame.display.flip()

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
