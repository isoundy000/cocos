import operator
import pprint
from math import radians, sin, cos

import cocos
import cocos.euclid as eu
import cocos.collision_model as cm

fe = 1.0e-4

class BaseActor(cocos.sprite.Sprite):
    # loadable subclasses should set
    # ingame_type_id = '...'

    @classmethod
    def new_from_dict(cls, game, args, description_dict):
        """
        don't modify, autority is editor

        args provides aditional positional arguments that must reach the
        __init__. These arguments don't come from the stored map, they are
        generated at game runtime just before calling here.
        Look at the manual for extra info

        description_dict carries the info for this instantiation comming
        from the stored level  
        """
        desc = description_dict
        ingame_type_id = description_dict.pop('ingame_type_id')
        editor_type_id = description_dict.pop('editor_type_id')
        combo_type = (editor_type_id, ingame_type_id)
        editor_img = game['roles']['actor'][combo_type]['editor_img']
        # it is a pyglet resource, so use '/' always to concatenate
        ingame_img = 'data/images/' + editor_img
        cx = description_dict.pop('cx')
        cy = description_dict.pop('cy')
        all_args = [ingame_img, cx, cy]
        all_args.extend(args) 
        actor = cls(*all_args, **description_dict)
        return actor

    def __init__(self, default_img, cx, cy,
                 # custom, all-subclasses, provided at run-time arguments
                 level,
                 # editor mandated, dont touch 
                 visible_width=32, others={}):
        """
        Adding or removing parameters must follow special rules to not break
        load-store, look in the manual in secctions named 'Changing code'
        """
        # cx, cy, visible_width in world units
        super(BaseActor, self).__init__(default_img)
        center = eu.Vector2(cx, cy)
        self.cshape = cm.AARectShape(center, 1.0, 1.0)
        self.update_visible_width(visible_width)
        self.update_center(center)
        self.level = level
        # process 'others' if necesary
        #...

    def update_center(self, new_center):
        assert isinstance(new_center, eu.Vector2) 
        self.position = new_center
        self.cshape.center = new_center

    def update_visible_width(self, visible_width):
        self.visible_width = visible_width
        self.scale =  float(visible_width) / self.image.width
        rx = visible_width / 2.0
        ry = self.image.height / 2.0 * self.scale
        self.cshape.rx = rx
        self.cshape.ry = ry


class Player(BaseActor):
    ingame_type_id = 'player 00.01'

    def set_consts(self, consts):
        self.max_fastness = consts['max_fastness']
        self.accel = consts['accel']
        # not proper, but short. Move to init when overriden
        self.vel = eu.Vector2(0.0, 0.0)
        self.heading = eu.Vector2(0.0, 1.0)
        self.fastness = 0.0

    def on_enter(self):
        super(Player, self).on_enter()
        self.scroller = self.get_ancestor(cocos.layer.ScrollingManager)

    def update(self, dt):
        buttons = self.controller.buttons
        mx = (buttons['right'] - buttons['left'])
        my = (buttons['up'] - buttons['down'])
        old_vel = self.vel
        if mx!=0 or my!=0:
            vel = old_vel + (dt * self.accel )* eu.Vector2(mx, my)
            fastness = vel.magnitude()
            if fastness > fe:
                self.heading = vel / fastness
            if fastness > self.max_fastness:
                vel = self.heading * self.max_fastness
            self.vel = vel
        # chopiness with pyglet 1.1.4 release, looks right with 1.2dev
        # I see dt more inestable with 1.1.4, even if fps ~57-60 with vsync
        # I know there have been code changes related to dt, also the pyglet
        # issue tracker shows a report about dt instability with some ATI
        # divers which can apply here. I will not upgrade just now, must be
        # further investigated

        # simpler, more sensitive to irregular dt, looks right with pyglet 1.2dev 
        new_pos = self.cshape.center + dt * self.vel

        # teoricaly more stable with dt variations, at least when accelerating
        # paralell to the axis, but remains chopy with pyglet 1.1.4
        #new_pos = self.cshape.center + dt * (old_vel + (0.5 * dt * self.accel) * self.heading)

        # new_pos not clamped, maps should protect the borders with trees
        self.update_center(new_pos)

        # this should be upgraded to something like the autoscroll in protoeditor
        # but that should probably wait till the fix for scroller intifier prob.
        self.scroller.set_focus(*new_pos)
        

class EnemyWanderer(BaseActor):
    """
    The most simplest behavior. (im late to release deadline)
    The bot has two states:
        wandering : choses a random direction, walks in that direction,
                    if it sees player changes to the state chasing
        chasing : walk heading to the current player position, if player goes
                  out of sight change to state wandering

    The states would update heading and maybe fastness, which will be used
    by update_position
    """
    ingame_type_id = 'wanderer 00.01'

    def __init__(self, *args, **kwargs):
        super(EnemyWanderer, self).__init__(*args, **kwargs)
        self.state = None
        self.go_state('wandering', *args)

    def enter_wandering(self):
        """
        chose a random direction to start to walk
        set fastness goal as max_wandering_fastness. A bit of random here ?  
        """
        pass

    def e_wandering(self):
        """
        if player near than Z and visible, go state chasing
        if collision with tree, do an enter wandering
        --
        looking for player may be better if done in reverse form:
        player call for all enemies near than Z and calls a player_near method
        in enemy
        """
        pass

    def enter_chasing(self):
        """
        set fastness goal as max_chasing_fastness
        """
        pass

    def e_chasing(self)
        """
        if player out of sight, go state wandering
        if collision with tree, go state wandering
        """
        pass

class EnemyChained(BaseActor):
    """
    Same as wanderer, but don't moves away of it spawn point
    more than certain distance
    """
    ingame_type_id = 'chained mons 00.01'

class Tree(BaseActor):
    ingame_type_id = 'tree 00.01'
    # old lime, best green
    eu_colors = [eu.Vector3(149,171,63), eu.Vector3(9,216,6)]

    def set_color_lerp_fraction(self, r):
        eu_color3 = r*Tree.eu_colors[0] + (1.0 - r)*Tree.eu_colors[1]
        color3 = [int(c) for c in eu_color3]
        self.color = color3

class Jewel(BaseActor):
    ingame_type_id = 'jewel 00.01'
    
