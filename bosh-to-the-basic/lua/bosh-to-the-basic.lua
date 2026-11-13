--[[
To call this script in Conky, use the following (assuming that you save this script to ~/.config/conky/bosh-to-the-basic/lua/bosh-to-the-basic.lua):
	lua_load = '~/.config/conky/bosh-to-the-basic/lua/bosh-to-the-basic.lua',
    lua_draw_hook_pre = 'conky_main'
]]

g_main_colour = "0xa8a8a8"
home_dir = os.getenv("HOME") or "."


require 'cairo'
require 'cairo_xlib'


-- global helper functions
function rgb_to_r_g_b(colour, alpha)
    return ((colour / 0x10000) % 0x100) / 255., ((colour / 0x100) % 0x100) / 255., (colour % 0x100) / 255., alpha
end


function to_boolean(p_str)
    if p_str == "true" or p_str == "True" then
        return true
    elseif p_str == "false" or p_str == "False" then
        return false
    else
        return false
    end
end


line_settings = {
    -- vertical
    { x1 = 30, y1 = 0, x2 = 30, y2 = 750 },
    { x1 = 140, y1 = 0, x2 = 140, y2 = 750 },
    { x1 = 250, y1 = 0, x2 = 250, y2 = 750 },
    { x1 = 275, y1 = 0, x2 = 275, y2 = 750 },
    { x1 = 536, y1 = 0, x2 = 536, y2 = 750 },

    -- horizontal
    { x1 = 0, y1 = 30, x2 = 470, y2 = 30 },
    { x1 = 0, y1 = 60, x2 = 470, y2 = 60 },
    { x1 = 0, y1 = 118, x2 = 470, y2 = 118 },
    { x1 = 0, y1 = 406, x2 = 270, y2 = 406 },
    { x1 = 0, y1 = 508, x2 = 270, y2 = 508 },
    { x1 = 0, y1 = 610, x2 = 270, y2 = 610 },
    { x1 = 0, y1 = 710, x2 = 270, y2 = 710 },
}


circle_settings = {
    { x = 230, y = 50, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 50, y = 230, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 230, y = 280, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 50, y = 460, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 230, y = 510, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 50, y = 690, radius = 18.0, start_angle = 0.0, end_angle = 360.0 },

    { x = 30, y = 255, radius = 50.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 250, y = 255, radius = 50.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 30, y = 485, radius = 50.0, start_angle = 0.0, end_angle = 360.0 },
    { x = 250, y = 485, radius = 50.0, start_angle = 0.0, end_angle = 360.0 },

    -- { x = 140, y = 140, radius = 75.0, start_angle = 0.0, end_angle = 360.0 },
    -- { x = 140, y = 370, radius = 75.0, start_angle = 0.0, end_angle = 360.0 },
    -- { x = 140, y = 600, radius = 75.0, start_angle = 0.0, end_angle = 360.0 },

    -- { x = 140, y = 140, radius = 25.0, start_angle = 0.0, end_angle = 360.0 },
    -- { x = 140, y = 370, radius = 25.0, start_angle = 0.0, end_angle = 360.0 },
    -- { x = 140, y = 600, radius = 11.0, start_angle = 0.0, end_angle = 360.0 },
}


function draw_elements(line_sketches_toggle)
    local function draw_lines(cr)
        for x in pairs(line_settings) do
            local l_item = line_settings[x]
            
            cairo_move_to (cr, l_item.x1, l_item.y1)
            cairo_line_to (cr, l_item.x2, l_item.y2)
            cairo_stroke (cr)
        end
    end
    
    
    local function draw_circles(cr)
        -- xc = 250.0
        -- yc = 255.0
        -- radius = 50.0
        -- angle1 = 0.0  * (2 * math.pi / 360) - math.pi / 2
        -- angle2 = 360.0 * (2 * math.pi / 360) - math.pi / 2
    
        for x in pairs(circle_settings) do
            local c_item = circle_settings[x]
            
            local angle_s = c_item.start_angle * (2 * math.pi / 360) - math.pi / 2
            local angle_e = c_item.end_angle * (2 * math.pi / 360) - math.pi / 2
    
            cairo_arc (cr, c_item.x, c_item.y, c_item.radius, angle_s, angle_e)
            cairo_stroke (cr)
        end
    end
    
    
    local function draw_line_sketches(cr, line_sketches_toggle)
        if to_boolean(line_sketches_toggle) == false then 
            return
        end
    
        local line_colour, line_alpha, line_thick = g_main_colour, 0.25, 1.0
    
        cairo_set_source_rgba(cr, rgb_to_r_g_b(line_colour, line_alpha))
        cairo_set_line_width(cr, line_thick)
        
        draw_lines(cr)
        draw_circles(cr)
    end
    
    
    -- this is to solve transparent issue when render logo with conky image object
    local function draw_logo(cr)
        local w, h = 0, 0
        local imagefile = home_dir .. "/.config/conky/bosh-to-the-basic/images/distro-1a.png"
        local image = cairo_image_surface_create_from_png (imagefile)
    
        w = cairo_image_surface_get_width (image)
        h = cairo_image_surface_get_height (image)
    
        cairo_translate (cr, 495.0, 30.0)
        -- cairo_rotate (cr, 45* math.pi/180)
        cairo_scale  (cr, 40.0/w, 40.0/h)
        -- cairo_translate (cr, -0.5*w, -0.5*h)
    
        cairo_set_source_surface (cr, image, 0, 0)
        cairo_paint (cr)
        cairo_surface_destroy (image)
    end


    if conky_window == nil then return end

    local cs = cairo_xlib_surface_create(conky_window.display,
        conky_window.drawable,
        conky_window.visual,
        conky_window.width,
        conky_window.height)
    local cr = cairo_create(cs)

    draw_line_sketches(cr, line_sketches_toggle)
    draw_logo(cr)           -- logo needs to be render last due to cairo_set_source_surface

    cairo_surface_destroy(cs)
    cairo_destroy(cr)
end


function conky_main(line_sketches_toggle)
    draw_elements(line_sketches_toggle)
end