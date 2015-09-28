require "util"
require "defines"
require "tfc"

function whistle_short()
  return {
    type = "play-sound",
    sound =
    {
      {
        filename = "__train_whistle__/resources/whistle_short.mp3",
        volume = 0.75
      },
    }
  }
end

function whistle_long()
  return {
    type = "play-sound",
    sound =
    {
      {
        filename = "__train_whistle__/resources/whistle_long.mp3",
        volume = 0.75
      },
    }
  }
end

--[[
game.on_event(defines.events.on_init, function(event)
	-- TODO
	-- Load trains table from global[]
end)
--]]

game.on_event(defines.events.on_tick, function(event)
	if game.player.character then
		-- we have a real character, not a ghost etc
		if game.player.character.vehicle and game.player.character.vehicle.name == "diesel-locomotive" then
			-- if we're in a train, don't bother computing the rest of it
			do return end
		end
		-- TODO: continue here!
	end
end)
