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