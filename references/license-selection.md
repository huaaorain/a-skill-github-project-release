# License selection

Ask the user to choose a license before the first public upload. Never silently choose one, infer that MIT is always appropriate, or describe a noncommercial license as open source.

## Decision flow

1. Check for an existing `LICENSE`, `COPYING`, machine-readable package metadata, and the README license section.
2. Preserve an existing license unless the user explicitly asks to change it. A license change needs deliberate review because contributors and users may rely on the old terms.
3. If no license exists, present the choices below and wait for the user's selection.
4. After selection, add the exact standard license text, update the README and package metadata, and include required notices in distributed assets.
5. If the user chooses a noncommercial or proprietary model, label it as source-available or proprietary, not OSI open source.

## Widely used software licenses

| License | Commercial use and sale | Source-sharing obligation | Attribution / notices |
| --- | --- | --- | --- |
| MIT | Allowed | None | Preserve copyright and license notice |
| Apache-2.0 | Allowed | None | Preserve notices; includes an express patent grant |
| BSD-3-Clause | Allowed | None | Preserve copyright/license notice; no endorsement by contributors |
| MPL-2.0 | Allowed | Modified MPL-covered files must remain MPL and their source must be available | Preserve notices |
| GPL-3.0-only | Allowed | Distributed derivatives must provide source under GPL | Preserve notices |
| AGPL-3.0-only | Allowed | Adds source-offer requirements for network use | Preserve notices |

The user can sell software under copyleft licenses, but recipients receive the rights granted by that license. No OSI-approved open-source license can prohibit all commercial use or resale.

## If commercial use or selling must be prohibited

Explain that this is a source-available or proprietary licensing decision, not an open-source license. Offer these choices without recommending one automatically:

- **PolyForm Noncommercial 1.0.0** — permits noncommercial use and modification while reserving commercial rights for a separate license. It is not OSI open source.
- **CC BY-NC 4.0** — requires attribution and prohibits primarily commercial use. It is designed for creative works, not software, and should not be presented as a software-license best practice.
- **Proprietary / no license** — no permission is granted by default beyond rights provided by applicable law.
- **Commercial-license agreement** — a lawyer-reviewed agreement can grant paid commercial rights while a separate noncommercial license covers personal use.

There is no standard OSI license that exactly means “use and modify with attribution, but never sell.” If the user requires those exact terms, explain the distinction and ask whether they want a source-available license, a custom commercial agreement, dual licensing, or a standard open-source license with commercial use permitted.

## Suggested user prompt

```text
项目还没有选择许可证。请选择：
1. MIT（宽松，允许商用和销售）
2. Apache-2.0（宽松，含专利授权）
3. BSD-3-Clause（宽松，禁止借作者名义背书）
4. MPL-2.0（文件级 copyleft）
5. GPL-3.0-only（强 copyleft）
6. AGPL-3.0-only（网络使用也触发源代码要求）
7. PolyForm Noncommercial 1.0.0（禁止商业用途，但不是开源协议）
8. CC BY-NC 4.0（要求署名且禁止商业用途，但不推荐用于软件）
9. 暂不授权 / 专有

如果你要求“允许使用和修改、保留署名、但禁止销售”，没有 OSI 开源协议完全符合；请明确选择来源可见或专有方案。
```

## Accuracy rules

- Say “open source” only for licenses approved by OSI.
- Do not alter MIT or another standard license to add a no-selling clause while keeping its name.
- Do not promise that a license prevents every commercial use; enforcement and legal interpretation depend on jurisdiction and facts.
- Do not provide legal advice as certainty. For commercial products or unusual terms, recommend qualified legal review.
