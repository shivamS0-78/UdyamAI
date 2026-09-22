export interface StateInfo {
  code: string;
  name: string;
  prioritySectors: string[];
  defaultDistricts: Array<{ id: string; name: string }>;
}

export const INDIAN_STATES: StateInfo[] = [
  {
    code: 'MH',
    name: 'Maharashtra',
    prioritySectors: ['Food Processing', 'Dairy', 'Textiles', 'Bio-Fertilizer', 'Jaggery Processing'],
    defaultDistricts: [
      { id: '624a9c93-78e1-4f68-b79b-0b865a45c1bf', name: 'Pune' },
      { id: 'dist-mh-ahmednagar', name: 'Ahmednagar' },
      { id: 'dist-mh-nashik', name: 'Nashik' },
      { id: 'dist-mh-solapur', name: 'Solapur' },
      { id: 'dist-mh-kolhapur', name: 'Kolhapur' },
    ],
  },
  {
    code: 'KA',
    name: 'Karnataka',
    prioritySectors: ['Jaggery Processing', 'Silk Weaving', 'Spices', 'Millets Value Addition', 'Coffee Agro-processing'],
    defaultDistricts: [
      { id: 'dist-ka-mandya', name: 'Mandya' },
      { id: 'dist-ka-belagavi', name: 'Belagavi' },
      { id: 'dist-ka-tumakuru', name: 'Tumakuru' },
      { id: 'dist-ka-dharwad', name: 'Dharwad' },
      { id: 'dist-ka-mysuru', name: 'Mysuru' },
    ],
  },
  {
    code: 'TN',
    name: 'Tamil Nadu',
    prioritySectors: ['Coir & Coconut Products', 'Turmeric Processing', 'Handloom & Textiles', 'Poultry'],
    defaultDistricts: [
      { id: 'dist-tn-erode', name: 'Erode' },
      { id: 'dist-tn-coimbatore', name: 'Coimbatore' },
      { id: 'dist-tn-thanjavur', name: 'Thanjavur' },
      { id: 'dist-tn-dindigul', name: 'Dindigul' },
      { id: 'dist-tn-salem', name: 'Salem' },
    ],
  },
  {
    code: 'UP',
    name: 'Uttar Pradesh',
    prioritySectors: ['Mentha Oil Distillation', 'Food Processing', 'Brassware & Crafts (ODOP)', 'Dairy'],
    defaultDistricts: [
      { id: 'dist-up-varanasi', name: 'Varanasi' },
      { id: 'dist-up-barabanki', name: 'Barabanki' },
      { id: 'dist-up-gorakhpur', name: 'Gorakhpur' },
      { id: 'dist-up-moradabad', name: 'Moradabad' },
      { id: 'dist-up-kannauj', name: 'Kannauj' },
    ],
  },
  {
    code: 'GJ',
    name: 'Gujarat',
    prioritySectors: ['Dairy & Milk Processing', 'Cumin & Spice Extraction', 'Groundnut Oil', 'Cotton Ginning'],
    defaultDistricts: [
      { id: 'dist-gj-anand', name: 'Anand' },
      { id: 'dist-gj-rajkot', name: 'Rajkot' },
      { id: 'dist-gj-surat', name: 'Surat' },
      { id: 'dist-gj-mehsana', name: 'Mehsana' },
      { id: 'dist-gj-kutch', name: 'Kutch' },
    ],
  },
  {
    code: 'RJ',
    name: 'Rajasthan',
    prioritySectors: ['Handicrafts & Block Print', 'Spices (Coriander/Cumin)', 'Guar Gum Processing', 'Camel Dairy'],
    defaultDistricts: [
      { id: 'dist-rj-jaipur', name: 'Jaipur' },
      { id: 'dist-rj-jodhpur', name: 'Jodhpur' },
      { id: 'dist-rj-bikaner', name: 'Bikaner' },
      { id: 'dist-rj-nagaur', name: 'Nagaur' },
      { id: 'dist-rj-kota', name: 'Kota' },
    ],
  },
  {
    code: 'PB',
    name: 'Punjab',
    prioritySectors: ['Agri-machinery & Tools', 'Food Processing', 'Hosiery & Garments', 'Dairy & Cattle Feed'],
    defaultDistricts: [
      { id: 'dist-pb-ludhiana', name: 'Ludhiana' },
      { id: 'dist-pb-amritsar', name: 'Amritsar' },
      { id: 'dist-pb-jalandhar', name: 'Jalandhar' },
      { id: 'dist-pb-bathinda', name: 'Bathinda' },
      { id: 'dist-pb-hoshiarpur', name: 'Hoshiarpur' },
    ],
  },
  {
    code: 'HR',
    name: 'Haryana',
    prioritySectors: ['Rice Milling & Export', 'Handloom & Furnishing', 'Mushroom Cultivation', 'Dairy Farming'],
    defaultDistricts: [
      { id: 'dist-hr-karnal', name: 'Karnal' },
      { id: 'dist-hr-hisar', name: 'Hisar' },
      { id: 'dist-hr-sonipat', name: 'Sonipat' },
      { id: 'dist-hr-sirsa', name: 'Sirsa' },
      { id: 'dist-hr-panipat', name: 'Panipat' },
    ],
  },
  {
    code: 'WB',
    name: 'West Bengal',
    prioritySectors: ['Jute & Eco-packaging', 'Tea Packaging & Value Addition', 'Handloom', 'Fish Aquaculture'],
    defaultDistricts: [
      { id: 'dist-wb-hooghly', name: 'Hooghly' },
      { id: 'dist-wb-murshidabad', name: 'Murshidabad' },
      { id: 'dist-wb-darjeeling', name: 'Darjeeling' },
      { id: 'dist-wb-nadia', name: 'Nadia' },
      { id: 'dist-wb-malda', name: 'Malda' },
    ],
  },
  {
    code: 'MP',
    name: 'Madhya Pradesh',
    prioritySectors: ['Soybean & Pulses Processing', 'Medicinal & Aromatic Herbs', 'Wheat Processing', 'Dairy & Ghee'],
    defaultDistricts: [
      { id: 'dist-mp-indore', name: 'Indore' },
      { id: 'dist-mp-ujjain', name: 'Ujjain' },
      { id: 'dist-mp-sehore', name: 'Sehore' },
      { id: 'dist-mp-jabalpur', name: 'Jabalpur' },
      { id: 'dist-mp-chhindwara', name: 'Chhindwara' },
    ],
  },
  {
    code: 'AP',
    name: 'Andhra Pradesh',
    prioritySectors: ['Chilli & Spice Processing', 'Aquaculture & Fish Processing', 'Silk Weaving', 'Mango Pulping'],
    defaultDistricts: [
      { id: 'dist-ap-guntur', name: 'Guntur' },
      { id: 'dist-ap-krishna', name: 'Krishna' },
      { id: 'dist-ap-eastgodavari', name: 'East Godavari' },
      { id: 'dist-ap-chittoor', name: 'Chittoor' },
      { id: 'dist-ap-anantapur', name: 'Anantapur' },
    ],
  },
  {
    code: 'TS',
    name: 'Telangana',
    prioritySectors: ['Turmeric Processing', 'Cotton Ginning', 'Poultry Farming', 'Handloom (Pochampally)'],
    defaultDistricts: [
      { id: 'dist-ts-warangal', name: 'Warangal' },
      { id: 'dist-ts-karimnagar', name: 'Karimnagar' },
      { id: 'dist-ts-nizamabad', name: 'Nizamabad' },
      { id: 'dist-ts-nalgonda', name: 'Nalgonda' },
      { id: 'dist-ts-khammam', name: 'Khammam' },
    ],
  },
  {
    code: 'KL',
    name: 'Kerala',
    prioritySectors: ['Spices Value Addition', 'Ayurvedic Formulations', 'Coir & Geotextiles', 'Coconut Processing'],
    defaultDistricts: [
      { id: 'dist-kl-wayanad', name: 'Wayanad' },
      { id: 'dist-kl-palakkad', name: 'Palakkad' },
      { id: 'dist-kl-idukki', name: 'Idukki' },
      { id: 'dist-kl-alappuzha', name: 'Alappuzha' },
      { id: 'dist-kl-thrissur', name: 'Thrissur' },
    ],
  },
  {
    code: 'BR',
    name: 'Bihar',
    prioritySectors: ['Makhana (Foxnut) Processing', 'Litchi Value Addition', 'Silk Handloom', 'Honey Production'],
    defaultDistricts: [
      { id: 'dist-br-muzaffarpur', name: 'Muzaffarpur' },
      { id: 'dist-br-bhagalpur', name: 'Bhagalpur' },
      { id: 'dist-br-darbhanga', name: 'Darbhanga' },
      { id: 'dist-br-nalanda', name: 'Nalanda' },
      { id: 'dist-br-purnia', name: 'Purnia' },
    ],
  },
  {
    code: 'OD',
    name: 'Odisha',
    prioritySectors: ['Millet Processing', 'Sambalpuri Handloom', 'Organic Coffee & Spices', 'Fisheries'],
    defaultDistricts: [
      { id: 'dist-od-sambalpur', name: 'Sambalpur' },
      { id: 'dist-od-ganjam', name: 'Ganjam' },
      { id: 'dist-od-koraput', name: 'Koraput' },
      { id: 'dist-od-balasore', name: 'Balasore' },
      { id: 'dist-od-mayurbhanj', name: 'Mayurbhanj' },
    ],
  },
  {
    code: 'AS',
    name: 'Assam',
    prioritySectors: ['Specialty Tea Processing', 'Eri & Muga Silk', 'Bamboo & Cane Crafts', 'Bhut Jolokia Spices'],
    defaultDistricts: [
      { id: 'dist-as-kamrup', name: 'Kamrup' },
      { id: 'dist-as-dibrugarh', name: 'Dibrugarh' },
      { id: 'dist-as-jorhat', name: 'Jorhat' },
      { id: 'dist-as-nagaon', name: 'Nagaon' },
      { id: 'dist-as-cachar', name: 'Cachar' },
    ],
  },
  {
    code: 'JH',
    name: 'Jharkhand',
    prioritySectors: ['Lac & Minor Forest Produce', 'Tussar Silk Processing', 'Organic Vegetables', 'Tribal Crafts'],
    defaultDistricts: [
      { id: 'dist-jh-ranchi', name: 'Ranchi' },
      { id: 'dist-jh-hazaribagh', name: 'Hazaribagh' },
      { id: 'dist-jh-deoghar', name: 'Deoghar' },
      { id: 'dist-jh-singhbhum', name: 'East Singhbhum' },
      { id: 'dist-jh-gumla', name: 'Gumla' },
    ],
  },
  {
    code: 'CG',
    name: 'Chhattisgarh',
    prioritySectors: ['Kosa Silk Processing', 'Bell Metal Crafts', 'Rice Milling & Bran Oil', 'Herbal Produce'],
    defaultDistricts: [
      { id: 'dist-cg-raipur', name: 'Raipur' },
      { id: 'dist-cg-durg', name: 'Durg' },
      { id: 'dist-cg-bastar', name: 'Bastar' },
      { id: 'dist-cg-bilaspur', name: 'Bilaspur' },
      { id: 'dist-cg-dhamtari', name: 'Dhamtari' },
    ],
  },
  {
    code: 'UK',
    name: 'Uttarakhand',
    prioritySectors: ['Himalayan Herbs & Nutraceuticals', 'Fruit Processing', 'Aromatic Oils', 'Organic Honey'],
    defaultDistricts: [
      { id: 'dist-uk-dehradun', name: 'Dehradun' },
      { id: 'dist-uk-haridwar', name: 'Haridwar' },
      { id: 'dist-uk-usnagar', name: 'Udham Singh Nagar' },
      { id: 'dist-uk-nainital', name: 'Nainital' },
      { id: 'dist-uk-almora', name: 'Almora' },
    ],
  },
  {
    code: 'HP',
    name: 'Himachal Pradesh',
    prioritySectors: ['Apple Concentrate & Fruit Processing', 'Kullu Shawls', 'Mushroom Cultivation', 'Herbal Extracts'],
    defaultDistricts: [
      { id: 'dist-hp-shimla', name: 'Shimla' },
      { id: 'dist-hp-kullu', name: 'Kullu' },
      { id: 'dist-hp-kangra', name: 'Kangra' },
      { id: 'dist-hp-solan', name: 'Solan' },
      { id: 'dist-hp-mandi', name: 'Mandi' },
    ],
  },
];
