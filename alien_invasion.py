import sys
import pygame
import self
from pygame import event

from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from time import sleep
from button import Button
from scoreboard import Scoreboard


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""

        pygame.init()
        """Create a display window on which we will draw all the game's graphical elements"""
        """self.screen is a surface. A surface in pygame is a part of the screen where a game element can be displayed.A surface return by display.set_mode(). 
        When we activate the game's animation loop, this surface will be redrawn on every pass through the loop, so it can be updated with any changes triggered by user input"""
        self.settings = Settings()

        # pass a size of (0,0) and the parameter pygame.FULLSCREEN. This tells Pygame to figure out a window size
        # that will fill the screen Because we don't know the full screen width and height, we use the width and
        # height atributes of the screen's rect to update the settings object.
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_high = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics.
        self.stats = GameStats(self)
        # Create a scoreboard
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        # Create a group to store all the live bullets so we can manage the bullets that have already been fired.
        # This group will be an instance of the pygame.sprite.Group class, which behaves like a list with some extra
        # functionality that's helpful when building games. We will use this group to draw bullets to the screen on
        # each pass throught the mail loop and to update each bullets's position
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # Make the Play button.
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Start the main loop for the game"""
        """The game is controlled by run_game(). A event is an action that the user performs while playing the game 
        such as pressing a key or moving the mouse """
        while True:
            # Watch for keyboard and mouse events.
            # We always need to call _check_events() in the while loop so we can immediately respond to user input even the game is inactive because
            # we still need to know if user press Q to quit the game.
            self._check_events()

            # These three functions only happen when the game is active. When the game is inactive, we don't need to update ship position.
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()


            self._update_screen()

    def _check_events(self):
        """Respond to keypresses and mouse events"""
        for event in pygame.event.get():
            """If click Quit, game exit"""
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # get_pos() return a tuple containing the mouse cursor's x and y when the mouse button is clicked
                # Then send the value to the method _check_play_button()
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
            # Whenever the player presss a key, that keypress is registered in pygame as an event. Each event is
            # picked up by the pygame.event.get() method

            # When the player presses the right arrow key, we want to move the ship to the right. We'll do this by
            # adjusting the ship's x-coordinate value"""
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            # Move the ship to the right.
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            """Press Q to exit"""
            sys.exit()
        # press space bar to fire bullets
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group"""
        # Make a instance of Bullet and call it new_bullet. Then add it to the group bullets using add() method. The add() method is similar as append(), but it is a special one for pygame
        # Check how many bullets exist before creating a new bullet.
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            # If bullet disappear from the top of the screen, remove it from the bullets group
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Responsd to bullet-alien collisions"""
        # Remove any bullets and aliens that have collided. Check for any bullets that have hit aliens. If so,
        # get rid of the bullet and the alien. The sprite.groupcollide() method compares the rects of each bullet and
        # alien in the two groups, and it returns a dictionary containing the bullets and aliens that have collided.
        # Each key in the dictionary is a bullet, and the corresponding value is the alien that was hit. If no
        # bullets hit an alien, groupcollide() returns an empty dictionary. In this case, we make sure the bullets
        # and aliens groups are both empty before creating a new fleet. True and True means if bullet hit alien,
        # they will get deleted. False True means if bullet hit alien, alien will be removed but bullet will stay
        # active until they diappeared.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, False, True)
        if collisions:
            # If one bullet hit multiple alliens or two bullets hit two allien at the same time, in order to make
            # score more accurate,get aliens list for each bullet.

            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)

            # Update the score
            self.sb.prep_score()
            self.sb.check_high_score()

        # Check whether the aliens group is empty. If so, we call empty() to remove all the remaining sprites from a
        # group. At this point, we start a new level.
        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Increase level
            self.stats.level += 1
            self.sb.prep_level()

    def _create_fleet(self):
        """Create the fleet of aliens"""
        # Create an alien and find the number of aliens in a row
        # Spacing between each alien is equal to one alien width
        # Make an alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_alien_x = available_space_x // (2 * alien_width)

        # Determine the number of rows of aliens that fit on the screen
        ship_height = self.ship.rect.height
        # row space = row height - first alien height - ship height - two alien heights from the bottom of the screen, so there is space above the ship
        # This design will give ship some time to shoot the aliens before they reach the ship
        available_space_y = (self.settings.screen_high - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # Create the full fleet of aliens
        for row_number in range(number_rows):
            for alien_number in range(number_alien_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        # Create an alien and place it in the row
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _update_aliens(self):
        """Check if the fleet is at an edge, then Update the positions of all aliens in the fleet"""
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.If no collisions, the method returns None. If there is a collision, it returns the alien that collided with the ship.
        # When an alien hit the ship, we need to delete all remanining aliens and bullets, and create a new fleet.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            print("Ship hit!!!")
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen"""
        # Redraw the screen during each pass through the loop
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        # The bullets.sprites() method returns a list of all sprites in the group bullets. To draw all fired bullets to the screen, we loop through the sprites in bullets and call draw_bullet() on each one
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        self.aliens.draw(self.screen)

        # Draw the score information.
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently drawn screen visible.

        pygame.display.flip()

    def _ship_hit(self):
            """Respond to the ship being hit by an alien"""
            # When an alien hits the ship, we'll substract one from the number of ships left, destory all existing aliens and bullets, create an
            # new fleet, and center the ship.We'll also pause the game for a moment to let the player notice the collision and regroup before a new fleet appears.
            # Decrement ships_left.
            if self.stats.ships_left > 0:
                self.stats.ships_left -= 1
                self.sb.prep_ships()

                # Get rid of any remaining aliens and bullets.
                self.aliens.empty()
                self.bullets.empty()

                # Create a new fleet and center the ship.
                self._create_fleet()
                self.ship.center_ship()

                # Add a puse after the updates have been made to all the game elements but before any changes have been drawn to the screen, so the player
                # can see that their ship has been hit.
                sleep(0.5)
            else:
                self.stats.game_active = False
                # Make mouse visible because it is about to click Play button
                pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
            """Check if any aliens have reached the bottom of the screen"""
            # If alien reaches the bottom of the screen, we'll treat it the same as if the ship got hit.
            screen_rect = self.screen.get_rect()
            for alien in self.aliens.sprites():
                if alien.rect.bottom >= screen_rect.bottom:
                    # Treat this the same as if the ship got hit.
                    self._ship_hit()
                    break

    def _check_play_button(self,mouse_pos):
        """Start a new game when the player clicks Play"""
        # We use collidepoint() to check whether the point of the mouse click overlaps the region defined by the Play button's rect.
        # If it does, we set game_active to True, and the game will start.
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()
            # Reset the game statistics.
            self.stats.reset_stats()
            self.stats.game_active = True
            # Reset the scoreboard images.
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)



if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()
