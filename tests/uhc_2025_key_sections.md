# UHC 2025 Key Authorization Rules - Easy Reference

## 📋 **File Locations:**
- **Full Markdown:** `data/processed/uhc_2025_test_20250916_092400.md` (58KB)
- **Extracted Rules:** `data/processed/UHC-Commercial-PA-Requirements-2025_rules_20250916_092400.json`
- **This Summary:** `tests/uhc_2025_key_sections.md`

## 🔍 **Key Authorization Rules Found in Document:**

### **1. ARTHROPLASTY (Joint Replacement Surgery)**
```
Arthroplasty Prior authorization required. 23470 23472 23473 23474
24360 24361 24362 24363
24365 24370 24371 25441
25442 25443 25444 25446
25449 27120 27125 27130
27132 27134 27137 27138
27437 27438 27440 27441
27442 27443 27445 27446
27447 27486 27487 27700
27702 27703
```
- **Status:** ❌ **MISSED BY ENHANCED PARSER**
- **Should Extract:** REQUIRED authorization + 38 CPT codes
- **Body Parts:** Shoulder (23xxx), Elbow (24xxx), Wrist (25xxx), Hip/Knee (27xxx)

### **2. ARTHROSCOPY (Minimally Invasive Surgery)**
```
Arthroscopy Prior authorization required. Prior authorization is required for all states.
. 29826 29843 29871
Prior authorization is required for all states. In addition, site of service will be
reviewed as part of the prior authorization process for the following codes
except in Alaska,Massachusets, Puerto Rico, Rhode Island, Texas, Utah, the
Virgin Islands and Wisconsin.
29805 29806 29807 29819
29820 29821 29822 29823
29824 29825 29827 29828
```
- **Status:** ❌ **MISSED BY ENHANCED PARSER**  
- **Should Extract:** REQUIRED authorization + 50+ CPT codes + Geographic exceptions
- **Geographic Exception:** NOT required in AK, MA, PR, RI, TX, UT, VI, WI

### **3. BREAST RECONSTRUCTION**
```
Arthroplasty (cont.) 19316 19318 19325 19328
19330 19340 19342 19350
19357 19361 19364 19367
19368 19369 19370 19371
19396 L8600
```
- **Status:** Partially extracted
- **Includes:** HCPCS code L8600 (breast implant)

### **4. CARDIAC/CARDIOVASCULAR**
```
A mechanical pump that 855-282-8929.
takes over the function 33927 33928 33929 33975
of the damaged
33976 33979 33981 33982
ventricle of the heart
and restores normal 33983
blood flow
```
- **Status:** ✅ **PARTIALLY EXTRACTED** (9 codes found)
- **Issue:** Classified as CONDITIONAL instead of REQUIRED

## 🔧 **How to View the Files:**

### **Option 1: Command Line (Works for sure)**
```bash
# View the full file
cat data/processed/uhc_2025_test_20250916_092400.md | less

# Search for specific content
grep -A5 -B5 "Prior authorization required" data/processed/uhc_2025_test_20250916_092400.md

# View specific sections
head -100 data/processed/uhc_2025_test_20250916_092400.md
```

### **Option 2: Copy to Desktop**
```bash
# Copy file to desktop for easier access
cp data/processed/uhc_2025_test_20250916_092400.md ~/Desktop/uhc_2025_markdown.md

# Open with your preferred text editor
open ~/Desktop/uhc_2025_markdown.md
```

### **Option 3: View in Browser**
```bash
# Convert to HTML for browser viewing
echo '<html><body><pre>' > ~/Desktop/uhc_2025.html
cat data/processed/uhc_2025_test_20250916_092400.md >> ~/Desktop/uhc_2025.html
echo '</pre></body></html>' >> ~/Desktop/uhc_2025.html
open ~/Desktop/uhc_2025.html
```

## 📊 **What You Should Look For:**

### **1. Authorization Language Patterns:**
- "Prior authorization required" (should be classified as REQUIRED)
- "Notification only" (should be NOTIFICATION_ONLY)  
- "Does not require" (should be NOT_REQUIRED)

### **2. CPT Code Patterns:**
- **5-digit codes:** 23470, 29826, 33776 (standard CPT)
- **HCPCS codes:** J0897, E0296, L8600 (letter + 4 digits)
- **Code ranges:** 29805-29825 (should be expanded)

### **3. Geographic Exceptions:**
- "except in Alaska, Massachusetts, Puerto Rico..."
- State abbreviations: AK, MA, PR, RI, TX, UT, VI, WI
- Should create geographic_exception chunks

### **4. Medical Categories:**
- Arthroplasty (joint replacement)
- Arthroscopy (scope procedures)  
- Cardiovascular (heart procedures)
- Breast reconstruction
- DME (durable medical equipment)

## 🎯 **Key Testing Commands:**

```bash
# Count authorization mentions
grep -c "Prior authorization required" data/processed/uhc_2025_test_20250916_092400.md

# Find all CPT codes  
grep -oE '\b[0-9]{5}\b' data/processed/uhc_2025_test_20250916_092400.md | sort -u | wc -l

# Find HCPCS codes
grep -oE '\b[A-Z][0-9]{4}\b' data/processed/uhc_2025_test_20250916_092400.md | sort -u

# Check geographic exceptions
grep -E '\b(Alaska|Massachusetts|Texas|Utah|Wisconsin)\b' data/processed/uhc_2025_test_20250916_092400.md

# Verify specific procedure codes
grep -E '\b(29826|29827|23470|33776)\b' data/processed/uhc_2025_test_20250916_092400.md
```

## 🚨 **Critical Issues Found:**

1. **Major Rules Missed:** Arthroplasty and Arthroscopy (core orthopedic procedures)
2. **Authorization Misclassification:** "Prior authorization required" → CONDITIONAL (should be REQUIRED)
3. **Geographic Exceptions Ignored:** Clear state exceptions not detected
4. **Rule Fragmentation:** Large rule sets split incorrectly

The enhanced parser needs significant fixes before production use!