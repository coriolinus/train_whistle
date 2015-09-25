require "util"
require "defines"

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

game.onevent(defines.events.ontick, function(event)
	if game.player.character then
		-- we have a real character, not a ghost etc
		if game.player.character.vehicle and game.player.character.vehicle.name == "diesel-locomotive" then
			-- if we're in a train, don't bother computing the rest of it
			do return end
		end
		
		-- find the nearby locomotives and act on them
		local everything = game.findentities{{game.player.character.position.x-5,
		                                      game.player.character.position.y-5},
                                             {game.player.character.position.x+5,
						                      game.player.character.position.y+5}}
		-- TODO: continue here!
	end
end)
