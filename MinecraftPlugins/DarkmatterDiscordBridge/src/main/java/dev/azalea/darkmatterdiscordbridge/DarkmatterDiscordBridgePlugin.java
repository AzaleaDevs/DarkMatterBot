package dev.azalea.darkmatterdiscordbridge;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.UUID;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.plugin.java.JavaPlugin;

public final class DarkmatterDiscordBridgePlugin extends JavaPlugin implements Listener {
    private HttpClient httpClient;
    private String botUrl;
    private String token;
    private String serverName;
    private int requestTimeoutSeconds;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        loadSettings();

        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(getConfig().getInt("connect-timeout-seconds", 5)))
            .build();

        getServer().getPluginManager().registerEvents(this, this);
        getLogger().info("DarkmatterDiscordBridge enabled");
    }

    private void loadSettings() {
        this.botUrl = getConfig().getString("bot-url", "http://127.0.0.1:8088/minecraft/player-join");
        this.token = getConfig().getString("token", "");
        this.serverName = getConfig().getString("server-name", "Minecraft");
        this.requestTimeoutSeconds = getConfig().getInt("request-timeout-seconds", 5);
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        sendJoinNotification(player.getName(), player.getUniqueId());
    }

    private void sendJoinNotification(String playerName, UUID playerUuid) {
        if (token == null || token.isBlank()) {
            getLogger().warning("Discord bot token is empty; skipping join notification");
            return;
        }

        String json = "{" +
            "\"player_name\":\"" + jsonEscape(playerName) + "\"," +
            "\"player_uuid\":\"" + jsonEscape(playerUuid.toString()) + "\"," +
            "\"server_name\":\"" + jsonEscape(serverName) + "\"" +
            "}";

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(botUrl))
            .timeout(Duration.ofSeconds(requestTimeoutSeconds))
            .header("Content-Type", "application/json")
            .header("X-Darkmatter-Token", token)
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();

        getServer().getScheduler().runTaskAsynchronously(this, () -> {
            try {
                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() < 200 || response.statusCode() >= 300) {
                    getLogger().warning("Discord bot returned HTTP " + response.statusCode() + ": " + response.body());
                }
            } catch (IOException exception) {
                getLogger().warning("Could not send join notification to Discord bot: " + exception.getMessage());
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                getLogger().warning("Join notification request was interrupted");
            } catch (IllegalArgumentException exception) {
                getLogger().warning("Invalid bot-url in config.yml: " + botUrl);
            }
        });
    }

    private static String jsonEscape(String value) {
        if (value == null) {
            return "";
        }

        return value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r");
    }
}
