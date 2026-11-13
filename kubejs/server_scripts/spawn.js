// Eldoria Dynamic Spawn & Lobby Management
const SPAWN_FILE_PATH = 'config/eldoria_spawn.json';

function getSpawn() {
    try {
        let Files = Java.loadClass('java.nio.file.Files');
        let Path = Java.loadClass('java.nio.file.Path');
        let p = Path.of(SPAWN_FILE_PATH);
        if (Files.exists(p)) {
            let str = Files.readString(p);
            let obj = JSON.parse(str);
            if (obj && obj.dimension) {
                return {
                    dimension: String(obj.dimension),
                    x: Number(obj.x),
                    y: Number(obj.y),
                    z: Number(obj.z),
                    yaw: Number(obj.yaw != null ? obj.yaw : 0.0),
                    pitch: Number(obj.pitch != null ? obj.pitch : 0.0)
                };
            }
        }
    } catch (e) {
        console.error('Error reading spawn file:', e);
    }
    return {
        dimension: 'eldoria:lobby',
        x: 210.5,
        y: 121.0,
        z: 150.5,
        yaw: 0.0,
        pitch: 0.0
    };
}

function saveSpawn(dim, x, y, z, yaw, pitch) {
    let spawn = {
        dimension: String(dim),
        x: Math.round(Number(x) * 100) / 100,
        y: Math.round(Number(y) * 100) / 100,
        z: Math.round(Number(z) * 100) / 100,
        yaw: Math.round(Number(yaw) * 10) / 10,
        pitch: Math.round(Number(pitch) * 10) / 10
    };
    try {
        let Files = Java.loadClass('java.nio.file.Files');
        let Path = Java.loadClass('java.nio.file.Path');
        let p = Path.of(SPAWN_FILE_PATH);
        if (p.getParent() != null) {
            Files.createDirectories(p.getParent());
        }
        Files.writeString(p, JSON.stringify(spawn, null, 2));
    } catch (e) {
        console.error('Error writing spawn file:', e);
    }
    return spawn;
}

PlayerEvents.loggedIn(event => {
    let player = event.player;
    if (!player.persistentData.getBoolean('eldoria_has_joined')) {
        player.persistentData.putBoolean('eldoria_has_joined', true);
        event.server.scheduleInTicks(15, () => {
            try {
                let sp = getSpawn();
                player.teleportTo(sp.dimension, sp.x, sp.y, sp.z, sp.yaw, sp.pitch);
                player.tell(Text.gold('═══════════════════════════════════════════════'));
                player.tell(Text.yellow('  Добро пожаловать в ') + Text.aqua('Eldoria TechnoMagic RPG') + Text.yellow('!'));
                player.tell(Text.gray('  Вы появились на главном спавне сервера.'));
                player.tell(Text.green('  Используйте команду ') + Text.yellow('/rtp') + Text.green(' для отправки в мир выживания!'));
                player.tell(Text.gold('═══════════════════════════════════════════════'));
            } catch (e) {
                console.error('Error on first join teleport:', e);
            }
        });
    }
});

ServerEvents.commandRegistry(event => {
    const { commands: Commands } = event;

    // /setspawn - sets the global server spawn point (OP only)
    event.register(
        Commands.literal('setspawn')
            .requires(s => s.hasPermission(2))
            .executes(ctx => {
                let player = ctx.source.player;
                if (!player) {
                    ctx.source.sendFailure(Text.red('Команду /setspawn может вызывать только игрок в игре!'));
                    return 0;
                }
                try {
                    let dim = 'eldoria:lobby';
                    try {
                        if (typeof player.level.dimension === 'function') {
                            dim = player.level.dimension().location().toString();
                        } else if (player.level.dimension && player.level.dimension.location) {
                            dim = player.level.dimension.location().toString();
                        } else {
                            dim = String(player.level.dimension);
                        }
                    } catch (dErr) {
                        try {
                            dim = player.level.dimension().toString();
                        } catch (dErr2) {}
                    }

                    let px = typeof player.getX === 'function' ? player.getX() : player.x;
                    let py = typeof player.getY === 'function' ? player.getY() : player.y;
                    let pz = typeof player.getZ === 'function' ? player.getZ() : player.z;
                    let pyaw = typeof player.getYRot === 'function' ? player.getYRot() : (player.yaw || 0);
                    let ppitch = typeof player.getXRot === 'function' ? player.getXRot() : (player.pitch || 0);

                    let sp = saveSpawn(dim, px, py, pz, pyaw, ppitch);
                    player.tell(Text.gold('[Eldoria] ') + Text.green('Главный спавн сервера успешно установлен!'));
                    player.tell(Text.gray('  Мир: ') + Text.yellow(sp.dimension) + Text.gray(' | X: ') + Text.yellow(sp.x) + Text.gray(' | Y: ') + Text.yellow(sp.y) + Text.gray(' | Z: ') + Text.yellow(sp.z));
                    return 1;
                } catch (err) {
                    console.error('Error executing /setspawn:', err);
                    player.tell(Text.red('Ошибка выполнения /setspawn: ' + err));
                    return 0;
                }
            })
    );

    // /spawn - teleports player to global server spawn
    event.register(
        Commands.literal('spawn')
            .executes(ctx => {
                let player = ctx.source.player;
                if (player) {
                    try {
                        let sp = getSpawn();
                        player.teleportTo(sp.dimension, sp.x, sp.y, sp.z, sp.yaw, sp.pitch);
                        player.tell(Text.green('Телепортация на спавн...'));
                    } catch (err) {
                        player.tell(Text.red('Ошибка телепортации: ' + err));
                    }
                }
                return 1;
            })
    );

    // /lobby - alias for spawn
    event.register(
        Commands.literal('lobby')
            .executes(ctx => {
                let player = ctx.source.player;
                if (player) {
                    try {
                        let sp = getSpawn();
                        player.teleportTo(sp.dimension, sp.x, sp.y, sp.z, sp.yaw, sp.pitch);
                        player.tell(Text.green('Телепортация в главное лобби...'));
                    } catch (err) {
                        player.tell(Text.red('Ошибка телепортации: ' + err));
                    }
                }
                return 1;
            })
    );
});
