import type { Metadata } from "next";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Settings",
};

export default function SettingsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-bone border-b border-ink/8 px-8 py-5">
        <h1 className="text-lg font-semibold text-ink tracking-tight">
          Settings
        </h1>
        <p className="text-sm text-ink-400 mt-0.5">
          Workspace and account preferences.
        </p>
      </div>

      <div className="px-8 py-6 max-w-2xl space-y-10">
        {/* Organization */}
        <SettingsSection title="Organization">
          <SettingsField
            label="Organization name"
            description="Displayed in the sidebar and exports."
          >
            <input
              type="text"
              defaultValue="Acme Corp"
              className="settings-input"
            />
          </SettingsField>
          <SettingsField
            label="Default workspace timezone"
            description="Used for timestamps in exports and reports."
          >
            <select className="settings-input">
              <option>UTC</option>
              <option>America/New_York</option>
              <option>Europe/London</option>
              <option>Asia/Singapore</option>
            </select>
          </SettingsField>
          <div className="flex justify-end">
            <Button size="sm">Save organization settings</Button>
          </div>
        </SettingsSection>

        {/* AI scoring */}
        <SettingsSection title="AI scoring">
          <SettingsField
            label="Default scoring model"
            description="Model used for candidate analysis. GPT-4o is recommended."
          >
            <select className="settings-input">
              <option>gpt-4o (recommended)</option>
              <option>gpt-4o-mini (faster, lower cost)</option>
            </select>
          </SettingsField>
          <SettingsField
            label="Confidence threshold"
            description="Criteria below this threshold are flagged as weak evidence."
          >
            <select className="settings-input">
              <option>70 (default)</option>
              <option>60 (lenient)</option>
              <option>80 (strict)</option>
            </select>
          </SettingsField>
          <SettingsField
            label="Auto-extract criteria from JD"
            description="Automatically detect requirements when a job description is uploaded."
          >
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded border-ink/20 text-ink focus:ring-ink/20"
              />
              <span className="text-sm text-ink">Enabled</span>
            </label>
          </SettingsField>
          <div className="flex justify-end">
            <Button size="sm">Save AI settings</Button>
          </div>
        </SettingsSection>

        {/* Integrations */}
        <SettingsSection title="Integrations">
          <IntegrationRow
            name="Microsoft Entra ID"
            description="Used for authentication. Connected."
            status="connected"
          />
          <IntegrationRow
            name="Greenhouse"
            description="Sync candidates from your ATS."
            status="disconnected"
          />
          <IntegrationRow
            name="Lever"
            description="Sync candidates from your ATS."
            status="disconnected"
          />
        </SettingsSection>

        {/* Danger zone */}
        <SettingsSection title="Danger zone">
          <div className="rounded-md border border-signal-red/20 p-4 space-y-3">
            <div>
              <p className="text-sm font-medium text-ink">Delete workspace</p>
              <p className="text-xs text-ink-400 mt-0.5">
                Permanently delete this workspace and all associated roles,
                candidates, and scores. This action cannot be undone.
              </p>
            </div>
            <Button size="sm" variant="danger">
              Delete workspace
            </Button>
          </div>
        </SettingsSection>
      </div>
    </div>
  );
}

function SettingsSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-5">
      <div className="border-b border-ink/8 pb-2">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  );
}

function SettingsField({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[1fr_220px] gap-6 items-start">
      <div>
        <p className="text-sm font-medium text-ink">{label}</p>
        <p className="text-xs text-ink-400 mt-0.5 leading-relaxed">
          {description}
        </p>
      </div>
      <div>{children}</div>
    </div>
  );
}

function IntegrationRow({
  name,
  description,
  status,
}: {
  name: string;
  description: string;
  status: "connected" | "disconnected";
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="text-sm font-medium text-ink">{name}</p>
        <p className="text-xs text-ink-400">{description}</p>
      </div>
      <div className="flex items-center gap-3">
        <span
          className={`text-xs font-medium ${
            status === "connected" ? "text-signal-green" : "text-ink-300"
          }`}
        >
          {status === "connected" ? "Connected" : "Not connected"}
        </span>
        <Button size="sm" variant="secondary">
          {status === "connected" ? "Disconnect" : "Connect"}
        </Button>
      </div>
    </div>
  );
}
