local settled = { blocked = true, done = true, error = true }

local function watched(block_id)
  if rex.args.block ~= nil then
    return block_id == rex.args.block
  end

  return block_id ~= rex.block_id
end

local function finished(ev)
  if ev.name == "program_status_removed" then
    return true
  end

  return ev.name == "program_status_changed" and ev.record ~= nil and settled[ev.record.state]
end

local ev, ctx = rex.wait("block_event", function(ev, ctx)
  return watched(ctx.block_id) and finished(ev)
end, rex.args.seconds or 600)

if ev == nil then
  return { timeout = true }
end

return { session_id = ctx.session_id, block_id = ctx.block_id, event = ev.name, record = ev.record }
