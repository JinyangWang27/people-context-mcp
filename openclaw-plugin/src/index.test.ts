import { getToolPluginMetadata } from "openclaw/plugin-sdk/tool-plugin";
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import plugin, { parseMcpToolResult, serverUrl } from "./index.js";

const PROPERTY_TEST_OPTIONS = { numRuns: 250, seed: 20260721 };
const nonNullJsonValue = fc.jsonValue().filter((value) => value !== null);

describe("people-context plugin", () => {
  it("exports the expected tools and keeps writes optional", () => {
    const metadata = getToolPluginMetadata(plugin);

    expect(metadata?.tools.map((tool) => tool.name)).toEqual([
      "people_resolve",
      "people_context",
      "people_communication_guidance",
      "people_remember",
    ]);
    expect(metadata?.tools.find((tool) => tool.name === "people_remember")).toMatchObject({
      optional: true,
    });
    expect(metadata?.tools.find((tool) => tool.name === "people_context")?.parameters).not.toHaveProperty(
      "properties.include_sensitive",
    );
  });

  it("builds the default and configured MCP URLs", () => {
    expect(serverUrl({}).toString()).toBe("http://127.0.0.1:8765/mcp");
    expect(
      serverUrl({ baseUrl: "http://localhost:9000/", path: "/people/mcp" }).toString(),
    ).toBe("http://localhost:9000/people/mcp");
    expect(
      serverUrl({ baseUrl: "http://localhost:9000////", path: "///people/mcp" }).toString(),
    ).toBe("http://localhost:9000/people/mcp");
  });

  it("prefers structured content and parses JSON text", () => {
    expect(
      parseMcpToolResult({ structuredContent: { candidates: [] } }, "resolve_person"),
    ).toEqual({ candidates: [] });
    expect(
      parseMcpToolResult(
        { content: [{ type: "text", text: '{"created":true}' }] },
        "remember_person",
      ),
    ).toEqual({ created: true });
  });

  it("preserves plain text and surfaces MCP tool errors", () => {
    expect(
      parseMcpToolResult(
        { content: [{ type: "text", text: "plain response" }] },
        "get_person_context",
      ),
    ).toBe("plain response");

    expect(() =>
      parseMcpToolResult(
        {
          isError: true,
          content: [{ type: "text", text: "person not found" }],
        },
        "get_person_context",
      ),
    ).toThrow('MCP tool "get_person_context" failed: person not found');
  });

  it("preserves arbitrary structured JSON values", () => {
    fc.assert(
      fc.property(nonNullJsonValue, (structuredContent) => {
        expect(parseMcpToolResult({ structuredContent }, "property_test")).toStrictEqual(
          structuredContent,
        );
      }),
      PROPERTY_TEST_OPTIONS,
    );
  });

  it("round-trips arbitrary JSON text", () => {
    fc.assert(
      fc.property(fc.jsonValue(), (value) => {
        const json = JSON.stringify(value);

        expect(
          parseMcpToolResult({ content: [{ type: "text", text: json }] }, "property_test"),
        ).toStrictEqual(value);
      }),
      PROPERTY_TEST_OPTIONS,
    );
  });

  it("extracts text from arbitrary mixed content blocks", () => {
    fc.assert(
      fc.property(fc.array(fc.string(), { minLength: 1 }), (values) => {
        const expected = values.map((value) => `value:${value}`).join("\n").trim();
        const content = values.flatMap((value, index) => [
          { type: "image", data: index },
          { type: "text", text: `value:${value}` },
          null,
          { type: "text", text: index },
        ]);

        expect(parseMcpToolResult({ content }, "property_test")).toBe(expected);
      }),
      PROPERTY_TEST_OPTIONS,
    );
  });

  it("gives arbitrary structured content precedence over text", () => {
    fc.assert(
      fc.property(nonNullJsonValue, fc.string(), (structuredContent, text) => {
        expect(
          parseMcpToolResult(
            { structuredContent, content: [{ type: "text", text }] },
            "property_test",
          ),
        ).toStrictEqual(structuredContent);
      }),
      PROPERTY_TEST_OPTIONS,
    );
  });

  it("rejects arbitrary error results", () => {
    fc.assert(
      fc.property(fc.jsonValue(), fc.string(), (structuredContent, text) => {
        expect(() =>
          parseMcpToolResult(
            { isError: true, structuredContent, content: [{ type: "text", text }] },
            "property_test",
          ),
        ).toThrow('MCP tool "property_test" failed');
      }),
      PROPERTY_TEST_OPTIONS,
    );
  });
});
