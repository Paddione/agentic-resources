# Guide: rigging a layered PSB for 2D Animation from code

**Experimental.** Short C# examples for the parts of a 2D rig that are hard
to get right from the API alone. They are a guide, not a script to copy as
is: write the Unity editor script the request needs (a character, a tank
whose turret turns, a crate whose pieces break off, a boss whose plates
fall) from them, in the user's project. They were checked on Unity 6000.6
with 2D Animation 16.0.1 and PSD Importer 15.0.1; on other versions a
member can be renamed or moved: read the `error CS` lines and adapt.

The PSB comes from a sequence's local script (`portrait_layers.py rig`
writes one, with a sidecar of bones), or from any layered PSB the user has.
Unity's PSD Importer turns each layer into a sprite and the whole file into
a prefab; these snippets write bones, meshes and weights into that
importer's data, so the Skinning Editor is never opened.

## Rules for the script

Whatever the route (a sequence's PSB or one the user brings), the script
goes into the user's project, so:

- **Ask first.** Say what you will add (the folder below, and for
  `HangingChain` a runtime script, section 7) and wait for a yes; ask which
  project, and never make one unasked.
- **Editor only, run only through `-executeMethod`** (or the Unity CLI's
  way to run a method in an open Editor). It reads only the PSB and its
  sidecar, and writes only through that PSB's importer: no network, no
  process, no file outside the PSB's folder and the script's own folder.
- **Change nothing else:** no other script, no package version (adding a
  missing 2D package is asked for, below).
- **Header.** Start each file with a comment saying it was written for
  this project, with the Unity and package versions it compiled against,
  and what you changed from this guide (renamed members), so whoever opens
  it later can tell.
- **Three tries.** A try that does not compile, or that throws when it
  runs, counts. After three, delete the folder you created (only that: a
  compile error anywhere blocks Play mode), say so, report the errors, and
  give the user the PSB alone, which 2D Animation imports with every layer
  in place, to rig in the Skinning Editor.
- **Experimental:** say so when you offer it.

**Setup.** The project needs `com.unity.2d.animation` and
`com.unity.2d.psdimporter` (ask before adding either to
`Packages/manifest.json`). Everything goes in one folder,
`Assets/Editor/Rig2D/`: the assembly definition below (so a project
without those packages still compiles), `Rig2D.cs` with the snippets you
use, and one file per entry point (`Rig2D.Tank.cs`, `Rig2D.Portrait.cs`).
A later rig in the same project reuses that folder: keep `Rig2D.cs`
(add a snippet it lacks), and add or rewrite only that rig's entry point
file; a second folder or asmdef would be a second `Rig2D.Editor` assembly,
which does not compile.

```json
{
    "name": "Rig2D.Editor",
    "references": ["Unity.2D.Animation.Editor", "Unity.2D.Sprite.Editor"],
    "includePlatforms": ["Editor"],
    "autoReferenced": false,
    "defineConstraints": ["RIG2D_ANIMATION", "RIG2D_PSD"],
    "versionDefines": [
        {"name": "com.unity.2d.animation", "expression": "", "define": "RIG2D_ANIMATION"},
        {"name": "com.unity.2d.psdimporter", "expression": "", "define": "RIG2D_PSD"}
    ]
}
```

Every snippet below is a member of one static class:

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.U2D.Animation;
using UnityEditor.U2D.Sprites;
using UnityEngine;
using UnityEngine.U2D;

static partial class Rig2D
{
```

## 1. Every layer as its own sprite

The importer slices sprites from the layers only when asked, and skips
hidden layers (expression or damage states) unless told to import them.

```csharp
    public static void ImportLayers(string psbPath)
    {
        var importer = new SerializedObject(AssetImporter.GetAtPath(psbPath));
        var reslice = importer.FindProperty("m_ResliceFromLayer");
        var hidden = importer.FindProperty("m_ImportHiddenLayers");
        if (reslice == null || hidden == null)
            throw new ArgumentException($"{psbPath} is not a PSB imported by the PSD Importer");
        reslice.boolValue = hidden.boolValue = true;
        importer.ApplyModifiedPropertiesWithoutUndo();
        AssetImporter.GetAtPath(psbPath).SaveAndReimport();
    }
```

## 2. The importer's rig data

The PSB's bones, meshes and the character's parts live behind three data
providers; `Apply()` writes back whatever was set on them.

```csharp
    public static ISpriteEditorDataProvider Providers(string psbPath)
    {
        var factories = new SpriteDataProviderFactories();
        factories.Init();
        var provider = factories.GetSpriteEditorDataProviderFromObject(AssetImporter.GetAtPath(psbPath));
        provider.InitSpriteEditorDataProvider();
        return provider;   // GetDataProvider<ICharacterDataProvider>(), <ISpriteBoneDataProvider>(), <ISpriteMeshDataProvider>()
    }
```

## 3. Bones from heads and tails

Positions in PSD pixels (y down, as an image editor or the sidecar gives
them), parents before children (`-1` for a root). The character stores each
bone relative to its parent; the sprites need each bone's world head and
rotation, which come back too.

```csharp
    public static SpriteBone[] Bones(string[] names, Vector2[] heads, Vector2[] tails, int[] parents, float psdHeight,
        out Vector2[] worldHead, out Quaternion[] worldRot)
    {
        int n = names.Length;
        var bones = new SpriteBone[n];
        worldHead = new Vector2[n];
        worldRot = new Quaternion[n];
        for (int i = 0; i < n; ++i)
        {
            Vector2 head = new Vector2(heads[i].x, psdHeight - heads[i].y), along = new Vector2(tails[i].x, psdHeight - tails[i].y) - head;
            worldHead[i] = head;
            worldRot[i] = Quaternion.Euler(0, 0, Mathf.Atan2(along.y, along.x) * Mathf.Rad2Deg);
            int p = parents[i];
            Quaternion inv = p >= 0 ? Quaternion.Inverse(worldRot[p]) : Quaternion.identity;
            bones[i] = new SpriteBone
            {
                name = names[i], guid = GUID.Generate().ToString(), parentId = p, length = along.magnitude,
                position = p >= 0 ? (Vector3)(Vector2)(inv * (head - worldHead[p])) : (Vector3)head,
                rotation = p >= 0 ? inv * worldRot[i] : worldRot[i],
                color = Color.HSVToRGB(i / (float)n, 0.6f, 1f),
            };
        }
        return bones;
    }
```

## 4. A sprite that moves rigidly with one bone

For a part that does not bend: a turret, an armour plate, a crate piece,
an eye, a mouth. The sprite gets its own copy of the bone, in sprite space,
and a quad fully weighted to it.

```csharp
    public static int[] BindRigid(CharacterPart part, SpriteRect rect, int bone, SpriteBone[] bones, Vector2[] worldHead,
        Quaternion[] worldRot, ISpriteBoneDataProvider boneData, ISpriteMeshDataProvider meshData)
    {
        Vector2 origin = part.spritePosition.position;
        var b = bones[bone];
        boneData.SetBones(rect.spriteID, new List<SpriteBone> { new SpriteBone
            { name = b.name, guid = b.guid, parentId = -1, length = b.length, position = worldHead[bone] - origin, rotation = worldRot[bone], color = b.color } });
        float w = part.spritePosition.width, h = part.spritePosition.height;
        var all = new BoneWeight { boneIndex0 = 0, weight0 = 1f };
        meshData.SetVertices(rect.spriteID, new[] { new Vertex2DMetaData { position = new Vector2(0, 0), boneWeight = all },
            new Vertex2DMetaData { position = new Vector2(w, 0), boneWeight = all }, new Vertex2DMetaData { position = new Vector2(w, h), boneWeight = all },
            new Vertex2DMetaData { position = new Vector2(0, h), boneWeight = all } });
        meshData.SetIndices(rect.spriteID, new[] { 0, 1, 2, 0, 2, 3 });
        meshData.SetEdges(rect.spriteID, new[] { new Vector2Int(0, 1), new Vector2Int(1, 2), new Vector2Int(2, 3), new Vector2Int(3, 0) });
        return new[] { bone };   // the part's bones (CharacterPart.bones)
    }
```

## 5. A sprite that bends over several bones

For hair, a cape, a tail, a banner: a grid over the sprite, each vertex
weighted by `weights`, which takes a point in the character's pixel space
(**y up**: for PSD pixels, as a sidecar gives them, use `psdHeight - p.y`)
and returns up to four (bone, weight) pairs. Weights that blend from one
bone to the next down the part make it bend instead of break. A vertex
`weights` gives no bone takes `fallback` (an all-zero weight collapses
under skinning).

```csharp
    public static int[] BindWeighted(CharacterPart part, SpriteRect rect, SpriteBone[] bones, Vector2[] worldHead, Quaternion[] worldRot,
        Func<Vector2, (int bone, float weight)[]> weights, int fallback, ISpriteBoneDataProvider boneData, ISpriteMeshDataProvider meshData, float step = 24f)
    {
        Vector2 origin = part.spritePosition.position;
        float w = part.spritePosition.width, h = part.spritePosition.height;
        int cols = Mathf.Max(1, Mathf.CeilToInt(w / step)), rows = Mathf.Max(1, Mathf.CeilToInt(h / step));
        var used = new List<int>();
        var verts = new Vertex2DMetaData[(cols + 1) * (rows + 1)];
        for (int r = 0; r <= rows; ++r)
            for (int c = 0; c <= cols; ++c)
            {
                var local = new Vector2(Mathf.Min(w, c * step), Mathf.Min(h, r * step));
                var pairs = weights(origin + local).Where(x => x.weight > 0).OrderByDescending(x => x.weight).Take(4).ToArray();
                if (pairs.Length == 0) pairs = new[] { (fallback, 1f) };   // no bone reaches it: never an all-zero weight
                float total = pairs.Sum(x => x.weight);
                var bw = new BoneWeight();
                for (int k = 0; k < pairs.Length; ++k)
                {
                    if (!used.Contains(pairs[k].bone)) used.Add(pairs[k].bone);
                    int slot = used.IndexOf(pairs[k].bone); float wt = pairs[k].weight / total;
                    if (k == 0) { bw.boneIndex0 = slot; bw.weight0 = wt; } else if (k == 1) { bw.boneIndex1 = slot; bw.weight1 = wt; }
                    else if (k == 2) { bw.boneIndex2 = slot; bw.weight2 = wt; } else { bw.boneIndex3 = slot; bw.weight3 = wt; }
                }
                verts[r * (cols + 1) + c] = new Vertex2DMetaData { position = local, boneWeight = bw };
            }
        var indices = new List<int>();
        for (int r = 0; r < rows; ++r)
            for (int c = 0; c < cols; ++c) { int a = r * (cols + 1) + c, d = a + cols + 1; indices.AddRange(new[] { a, a + 1, d + 1, a, d + 1, d }); }
        var edges = new List<Vector2Int>();
        for (int c = 0; c < cols; ++c) { edges.Add(new Vector2Int(c, c + 1)); edges.Add(new Vector2Int(rows * (cols + 1) + c, rows * (cols + 1) + c + 1)); }
        for (int r = 0; r < rows; ++r) { edges.Add(new Vector2Int(r * (cols + 1), (r + 1) * (cols + 1))); edges.Add(new Vector2Int(r * (cols + 1) + cols, (r + 1) * (cols + 1) + cols)); }
        boneData.SetBones(rect.spriteID, used.Select(i => new SpriteBone { name = bones[i].name, guid = bones[i].guid, parentId = -1,
            length = bones[i].length, position = worldHead[i] - origin, rotation = worldRot[i], color = bones[i].color }).ToList());
        meshData.SetVertices(rect.spriteID, verts);
        meshData.SetIndices(rect.spriteID, indices.ToArray());
        meshData.SetEdges(rect.spriteID, edges.ToArray());
        return used.ToArray();   // the part's bones, in the order the weights index them
    }
```

## 6. Swappable sprites (expressions, damage states)

Layers that replace each other (mouth shapes, eye states, a wall whole,
cracked, broken) become one Sprite Library category: the importer then
gives that group one GameObject with a `SpriteResolver`, and
`SetCategoryAndLabel(category, label)` picks the sprite. Each entry is
(category, label, layer name).

```csharp
    public static void Categories(string psbPath, (string category, string label, string layer)[] entries, SpriteRect[] rects)
    {
        var importer = new SerializedObject(AssetImporter.GetAtPath(psbPath));
        var list = importer.FindProperty("m_SpriteCategoryList.m_Categories");
        var groups = entries.GroupBy(e => e.category).ToList();
        list.arraySize = groups.Count;
        for (int g = 0; g < groups.Count; ++g)
        {
            var cat = list.GetArrayElementAtIndex(g);
            cat.FindPropertyRelative("m_Name").stringValue = groups[g].Key;
            var labels = cat.FindPropertyRelative("m_Labels");
            var items = groups[g].ToList();
            labels.arraySize = items.Count;
            for (int l = 0; l < items.Count; ++l)
            {
                labels.GetArrayElementAtIndex(l).FindPropertyRelative("m_Name").stringValue = items[l].label;
                labels.GetArrayElementAtIndex(l).FindPropertyRelative("m_SpriteId").stringValue = rects.First(r => r.name == items[l].layer).spriteID.ToString();
            }
        }
        importer.ApplyModifiedPropertiesWithoutUndo();
    }
```

## Putting it together: a tank whose turret turns

The order matters: import the layers, set the bones on the character, bind
each part, apply, then write the categories and reimport. End with one line
in this form, which is how a run is read (any layer no bone carries is
named after `unrigged:`):

`[Rig2D] rigged <psb>: <n> bones; unrigged: <layers, or none>`

```csharp
    // unity run "<project>" -- -executeMethod Rig2D.Tank -psb Assets/Tank/tank.psb
    public static void Tank()
    {
        string[] args = Environment.GetCommandLineArgs();
        int at = Array.IndexOf(args, "-psb");
        if (at < 0 || at + 1 >= args.Length) throw new ArgumentException("pass -psb Assets/<path>.psb");
        string psb = args[at + 1].Replace('\\', '/');
        if (!psb.StartsWith("Assets/") || !psb.EndsWith(".psb", StringComparison.OrdinalIgnoreCase) || psb.Contains(".."))
            throw new ArgumentException($"-psb {psb}: a .psb under Assets/");
        ImportLayers(psb);
        var provider = Providers(psb);
        var character = provider.GetDataProvider<ICharacterDataProvider>().GetCharacterData();
        var boneData = provider.GetDataProvider<ISpriteBoneDataProvider>();
        var meshData = provider.GetDataProvider<ISpriteMeshDataProvider>();
        var rects = provider.GetSpriteRects();
        var unrigged = new List<string>();
        // Hull: a root along the hull; turret: pivots at its ring, pointing along the barrel (PSD pixels).
        character.bones = Bones(new[] { "Hull", "Turret" }, new[] { new Vector2(100, 300), new Vector2(256, 230) },
            new[] { new Vector2(412, 300), new Vector2(420, 230) }, new[] { -1, 0 }, 512, out var head, out var rot);
        for (int p = 0; p < character.parts.Length; ++p)
        {
            var part = character.parts[p];
            var rect = rects.First(r => r.spriteID.ToString() == part.spriteId);
            if (rect.name != "Turret" && rect.name != "Hull") { unrigged.Add(rect.name); continue; }
            part.bones = BindRigid(part, rect, rect.name == "Turret" ? 1 : 0, character.bones, head, rot, boneData, meshData);
            character.parts[p] = part;
        }
        provider.GetDataProvider<ICharacterDataProvider>().SetCharacterData(character);
        provider.Apply();
        AssetImporter.GetAtPath(psb).SaveAndReimport();
        Debug.Log($"[Rig2D] rigged {psb}: {character.bones.Length} bones; unrigged: {(unrigged.Count > 0 ? string.Join(", ", unrigged) : "none")}");
    }
}
```

## 7. Hair that hangs and swings (a runtime component)

Bones only follow what drives them: hair bound to the head turns with it
like a helmet. Real hair keeps hanging down when the head tilts, and swings
a little after each move. This component does that each frame, after the
animation: every listed bone eases toward hanging straight down against its
parent's tilt since the start, with a spring. Use it on hair chains, a
cape, a tail, a hanging ribbon; leave out bones a clip animates. It is
runtime code (no `UnityEditor`), so it goes outside the `Editor` folder, in
its own file, and compiles into the user's game build: say that, and that
you will add it to their scene and save a prefab variant, and get a yes
before writing it.

```csharp
using UnityEngine;

[DefaultExecutionOrder(-50)]   // after the Animator, before the 2D Animation deformation
public class HangingChain : MonoBehaviour
{
    [System.Serializable] public class Link { public Transform bone; [Range(0, 1)] public float gravity = 0.6f; }
    public Link[] links;                     // e.g. hair: the first segments 0.6, their tips 0.5 (they swing more freely)
    public float stiffness = 60f, damping = 7f;
    Quaternion[] rest; float[] parentRest, angle, speed;

    void Start() => Capture();
    void LateUpdate() => Step(Time.deltaTime);

    public void Capture()                    // the pose the chains hang from: call again after a rebind
    {
        int n = links.Length;
        rest = new Quaternion[n]; parentRest = new float[n]; angle = new float[n]; speed = new float[n];
        for (int i = 0; i < n; ++i) { rest[i] = links[i].bone.localRotation; parentRest[i] = links[i].bone.parent.eulerAngles.z; }
    }

    public void Step(float dt)               // in small sub-steps: one long frame (a hitch, a 5 fps render) stays stable
    {
        if (rest == null || rest.Length != links.Length) Capture();   // batch mode runs no Start
        int n = Mathf.Max(1, Mathf.CeilToInt(dt / (1f / 120f)));
        for (int k = 0; k < n; ++k) SubStep(dt / n);
    }

    void SubStep(float dt)
    {
        for (int i = 0; i < links.Length; ++i)
        {
            var bone = links[i].bone;
            float tilt = Mathf.DeltaAngle(parentRest[i], bone.parent.eulerAngles.z);
            float target = -links[i].gravity * tilt;
            speed[i] += (stiffness * (target - angle[i]) - damping * speed[i]) * dt;
            angle[i] += speed[i] * dt;
            bone.localRotation = rest[i] * Quaternion.Euler(0, 0, angle[i]);
        }
    }
}
```

Add it to the character's instance in the scene (an imported PSB's own
prefab takes no components: save the instance as a prefab variant to keep
it), and list the chains' bones. In batch mode, where neither `Start` nor
`LateUpdate` runs, call `Step(1f / fps)` once per rendered frame (it
captures the rest pose on its first call).

## Check the result

A rig that imports can still be wrong. Log every layer no bone carries
(it stays still when the rest moves) and name it to the user. Then drag
the prefab into a scene and turn a bone or two: parts that should move
together move together, and nothing tears or shows a hole. Batch mode runs
no `LateUpdate`, so a render made from a script sees skinned sprites at
rest unless the script turns `SpriteSkin.alwaysUpdate` on and lets a frame
run; checking in an open Editor avoids that.
