mp.register_event("file-loaded", function()
    local vid = mp.get_property("vid")
    if vid == "no" then
        mp.set_property("lavfi-complex", "[aid1]asplit[ao][a];[a]showfreqs=s=1280x400:mode=line,format=yuv420p[v];[v]format=rgba[vo]")
    end
end)

