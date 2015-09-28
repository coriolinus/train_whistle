--[[
The code in this file was adapted from TheFatController, by James O'Farrell. 
Source here: https://github.com/jamesofarrell/TheFatController

Maintains a list of trains.
--]]

function getTrainInfoFromEntity(trains, entity)
	if trains ~= nil then
		for _, trainInfo in ipairs(trains) do
			if trainInfo ~= nil and trainInfo.train ~= nil and trainInfo.train.valid and entity == trainInfo.train.carriages[1] then
				return trainInfo
			end
		end
	end
end

function getLocomotives(train)
	if train ~= nil and train.valid then
		local locos = {}
		for i,carriage in ipairs(train.carriages) do
			if carriage ~= nil and carriage.valid and isTrainType(carriage.type) then
				table.insert(locos, carriage)
			end
		end
		return locos
	end
end

function getNewTrainInfo(train)
	if train ~= nil then
		local carriages = train.carriages
		if carriages ~= nil and carriages[1] ~= nil and carriages[1].valid then
			local newTrainInfo = {}
			newTrainInfo.train = train
			--newTrainInfo.firstCarriage = getFirstCarriage(train)
			newTrainInfo.locomotives = getLocomotives(train)
			
			--newTrainInfo.display = true
			return newTrainInfo
		end
	end
end

function getTrainInfoOrNewFromEntity(trains, entity)
	local trainInfo = getTrainInfoFromEntity(trains, entity)
	if trainInfo == nil then
		local newTrainInfo = getNewTrainInfo(entity.train)
		table.insert(trains, newTrainInfo)
		return newTrainInfo
	else
		return trainInfo
	end
end

entityBuilt = function(event)
	local entity = event.created_entity
	if entity.type == "locomotive" and global.unlocked then --or entity.type == "cargo-wagon"
		getTrainInfoOrNewFromEntity(global.trainsByForce[entity.force.name], entity)
	end
end

game.on_event(defines.events.on_built_entity, entityBuilt)
game.on_event(defines.events.on_robot_built_entity, entityBuilt)

game.on_event(defines.events.on_force_created, function(event)
	if global.trainsByForce ~= nil then
		global.trainsByForce[event.force.name] = {}
	end
end)

function isTrainInfoDuplicate(trains, trainInfoB, index)
	--local trainInfoB = trains[index]
	if trainInfoB ~= nil and trainInfoB.train ~= nil and trainInfoB.train.valid then
		for i, trainInfo in ipairs(trains) do
			--debugLog(i)
			if i ~= index and trainInfo.train ~= nil and trainInfo.train.valid and compareTrains(trainInfo.train, trainInfoB.train) then
				return true
			end
		end
	end
	
	
	return false
end

function compareTrains(trainA, trainB)
	if trainA ~= nil and trainA.valid and trainB ~= nil and trainB.valid and trainA.carriages[1] == trainB.carriages[1] then
		return true
	end
	return false
end

function updateTrains(trains)
	--if trains ~= nil then
		for i, trainInfo in ipairs(trains) do
			
			--refresh invalid train objects
			if trainInfo.train == nil or not trainInfo.train.valid then
				trainInfo.train = getTrainFromLocomotives(trainInfo.locomotives)
				trainInfo.locomotives = getLocomotives(trainInfo.train)
				if isTrainInfoDuplicate(trains, trainInfo, i) then
					trainInfo.train = nil
				end
			end
			
			if (trainInfo.train == nil or not trainInfo.train.valid) then
				
				table.remove(trains, i)
			else
				trainInfo.locomotives = getLocomotives(trainInfo.train)
				updateTrainInfo(trainInfo, game.tick)
				--debugLog(trainInfo.train.state)
			end
		end
	--end
end

function updateTrainInfoIfChanged(trainInfo, field, value) 
	if trainInfo ~= nil and field ~= nil and trainInfo[field] ~= value then
		trainInfo[field] = value
		trainInfo.updated = true
		return true
	end
	return false
end

function updateTrainInfo(trainInfo, tick)
	if trainInfo ~= nil then
		trainInfo.updated = false
	
		if trainInfo.lastState == nil or trainInfo.lastState ~= trainInfo.train.state then
			trainInfo.updated = true
			if trainInfo.train.state == 7 then
				trainInfo.lastStateStation = tick
			end
			trainInfo.lastState = trainInfo.train.state
			trainInfo.lastStateTick = tick
		end
		
		updateTrainInfoIfChanged(trainInfo, "manualMode", trainInfo.train.manual_mode)
		updateTrainInfoIfChanged(trainInfo, "speed", trainInfo.train.speed)
		
				--SET InventoryText (trainInfo.train.state == 9 or trainInfo.train.state == 7
		if (trainInfo.train.state == 7 or (trainInfo.train.state == 9 and trainInfo.train.speed == 0)) or not trainInfo.updatedInventory then
			local tempInventory = getHighestInventoryCount(trainInfo)
			trainInfo.updatedInventory = true
			if tempInventory ~= nil then
				updateTrainInfoIfChanged(trainInfo, "inventory", tempInventory)
			end
		end
		
		--SET CurrentStationText
		if trainInfo.train.schedule ~= nil and trainInfo.train.schedule.current ~= nil and trainInfo.train.schedule.current ~= 0 then
			if trainInfo.train.schedule.records[trainInfo.train.schedule.current] ~= nil then
				updateTrainInfoIfChanged(trainInfo, "currentStation", trainInfo.train.schedule.records[trainInfo.train.schedule.current].station)
			else
				updateTrainInfoIfChanged(trainInfo, "currentStation", "Auto")
			end
		end
		

		if trainInfo.train.schedule ~= nil and trainInfo.train.schedule.records ~= nil and trainInfo.train.schedule.records[1] ~= nil then
			trainInfo.stations = {}
			-- if trainInfo.stations == nil then
				
			-- end
			for i, record in ipairs(trainInfo.train.schedule.records) do
				trainInfo.stations[record.station] = true
			end
		else
			trainInfo.stations = nil
		end
	end
end

  -- -- normal state - following the path
  -- on_the_path = 0,
  -- -- had path and lost it - must stop
  -- path_lost = 1,
  -- -- doesn't have anywhere to go
  -- no_schedule = 2,
  -- -- has no path and is stopped
  -- no_path = 3,
  -- -- braking before the railSignal
  -- arrive_signal = 4,
  -- wait_signal = 5,
  -- -- braking before the station
  -- arrive_station = 6,
  -- wait_station = 7,
  -- -- switched to the manual control and has to stop
  -- manual_control_stop = 8,
  -- -- can move if user explicitly sits in and rides the train
  -- manual_control = 9,
  -- -- train was switched to auto control but it is moving and needs to be stopped
  -- stop_for_auto_control = 10

game.on_event(defines.events.on_train_changed_state, function(event)
	--debugLog("State Change - " .. game.tick)
	if not global.unlocked then --This is retarded, just set the event on unlock
		return
	end
	
	if global.trainsByForce == nil then
		global.trainsByForce = {}
	end
	
	if global.guiSettings == nil then
		return
	end
	
	local train = event.train
	local entity = train.carriages[1]
	
	
	if global.trainsByForce[entity.force.name] == nil then
		global.trainsByForce[entity.force.name] = {}
	end
	trains = global.trainsByForce[entity.force.name]
	local trainInfo = getTrainInfoOrNewFromEntity(trains, entity)
	if trainInfo ~= nil then
		local newtrain = false
		if trainInfo.updated == nil then
			newtrain = true
		else
		end
		updateTrainInfo(trainInfo,game.tick)
		if newtrain then
			for i,player in ipairs(game.players) do
				global.guiSettings[i].pageCount = getPageCount(trains, global.guiSettings[i]) 
			end
		end
		-- refreshAllTrainInfoGuis(global.trainsByForce, global.guiSettings, game.players, newtrain)
	end
end)