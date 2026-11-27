-- Only text measurement uses Cairo. OPT-01 does not install a draw hook.
require 'cairo'

local surface, cr, bosh_extents

function conky_bosh_shutdown()
    if cr then cairo_destroy(cr) end
    if surface then cairo_surface_destroy(surface) end
    cr, surface, bosh_extents = nil, nil, nil
end

function conky_bosh_percent(value)
    local n = tonumber(value)
    if n and n >= 0 and n <= 100 then return math.floor(n + 0.5) end
    return 0
end

local swap_checked, swap_present
function conky_bosh_swap_present()
    local now = os.time()
    if not swap_checked or now < swap_checked or now - swap_checked >= 10 then
        swap_checked = now
        swap_present = 0
        local swaps = io.open('/proc/swaps', 'r')
        if swaps then
            swaps:read('*l') -- Header
            if swaps:read('*l') then swap_present = 1 end
            swaps:close()
        end
    end
    return swap_present
end

function conky_bosh_center_row(mode, argument)
    if not cr then
        surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 1, 1)
        cr = cairo_create(surface)
        cairo_select_font_face(cr, "Noto Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)
        bosh_extents = cairo_text_extents_t:create()
        tolua.takeownership(bosh_extents)
    end
    local size = mode == "speed" and 9 or 8
    cairo_set_font_size(cr, size * 96 / 72)

    local function centered(value, center, color)
        cairo_text_extents(cr, value, bosh_extents)

        local x = math.floor(
            center - bosh_extents.width / 2
            - bosh_extents.x_bearing + 0.5
        )

        return "${goto " .. x .. "}"
            .. (color and "${color" .. color .. "}" or "")
            .. value .. "${color}"
    end

    local result = {}

    if mode == "cpu" then
        for n = 1, math.min(4, tonumber(argument) or 0) do
            local value = conky_parse(
                "${cpu cpu" .. n .. "}"
            )

            result[n] = centered(
                "C" .. n .. " " .. value .. "%",
                34 + (n - 1) * 67, 2
            )
        end

    elseif mode == "title" then
        result[1] = centered("BAJADA", 67.5, 3)
        result[2] = centered("SUBIDA", 201.5, 2)

    elseif mode == "speed" or mode == "total" then
        local iface = argument
        if iface and iface:match("^[%w_.:-]+$") then
            local down, up

            if mode == "speed" then
                down = conky_parse(
                    "${downspeed " .. iface .. "}"
                ) .. "/s"

                up = conky_parse(
                    "${upspeed " .. iface .. "}"
                ) .. "/s"
            else
                down = "Total: " .. conky_parse(
                    "${totaldown " .. iface .. "}"
                )

                up = "Total: " .. conky_parse(
                    "${totalup " .. iface .. "}"
                )
            end

            result[1] = centered(down, 67.5)
            result[2] = centered(up, 201.5)
        end
    end

    return table.concat(result)
end
