using IAuto.Inference;
using Microsoft.Extensions.AI;

namespace IAuto.Inference.Tests;

public sealed class ChatClientExtensionsTests
{
    [Fact]
    public async Task CompleteTextAsync_ReturnsAssistantText()
    {
        using var client = new StubChatClient { Reply = "hello world" };

        var text = await client.CompleteTextAsync("hi");

        Assert.Equal("hello world", text);
        Assert.NotNull(client.LastMessages);
        Assert.Single(client.LastMessages!);
        Assert.Equal(ChatRole.User, client.LastMessages![0].Role);
    }

    [Fact]
    public async Task CompleteTextAsync_PrependsSystemPrompt()
    {
        using var client = new StubChatClient();

        _ = await client.CompleteTextAsync("question", systemPrompt: "be terse");

        Assert.NotNull(client.LastMessages);
        Assert.Equal(2, client.LastMessages!.Count);
        Assert.Equal(ChatRole.System, client.LastMessages[0].Role);
        Assert.Equal(ChatRole.User, client.LastMessages[1].Role);
    }

    [Fact]
    public async Task CompleteTextAsync_BlankPrompt_Throws()
    {
        using var client = new StubChatClient();

        await Assert.ThrowsAsync<ArgumentException>(() => client.CompleteTextAsync("  "));
    }
}
