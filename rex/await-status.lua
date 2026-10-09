local wanted = { blocked = true, done = true, error = true }

local function watched(block_id)
  if rex.args.block ~= nil then
    return block_id == rex.args.block
  end

  return block_id ~= rex.block_id
end

local ev, ctx = rex.wait("terminal.program_status_changed", function(ev, ctx)
  return ev.record ~= nil and wanted[ev.record.state] and watched(ctx.block_id)
end, rex.args.seconds or 600)

if ev == nil then
  return { timeout = true }
end

return { session_id = ctx.session_id, block_id = ctx.block_id, record = ev.record }
