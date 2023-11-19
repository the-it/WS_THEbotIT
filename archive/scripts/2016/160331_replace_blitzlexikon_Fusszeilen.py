# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

site = pywikibot.Site()

pages = {"Seite:LA2-Blitz-0001.jpg":"i","Seite:LA2-Blitz-0002.jpg":"ii","Seite:LA2-Blitz-0003.jpg":"iii","Seite:LA2-Blitz-0004.jpg":"iv","Seite:LA2-Blitz-0005.jpg":"1–2","Seite:LA2-Blitz-0006.jpg":"3–4","Seite:LA2-Blitz-0007.jpg":"5–6","Seite:LA2-Blitz-0008.jpg":"Tafel","Seite:LA2-Blitz-0009.jpg":"Tafel","Seite:LA2-Blitz-0010.jpg":"Tafel","Seite:LA2-Blitz-0011.jpg":"Tafel","Seite:LA2-Blitz-0012.jpg":"Tafel","Seite:LA2-Blitz-0013.jpg":"9–10","Seite:LA2-Blitz-0014.jpg":"11–12","Seite:LA2-Blitz-0015.jpg":"13–14","Seite:LA2-Blitz-0016.jpg":"15–16","Seite:LA2-Blitz-0017.jpg":"17–18","Seite:LA2-Blitz-0018.jpg":"19–20","Seite:LA2-Blitz-0019.jpg":"21–22","Seite:LA2-Blitz-0020.jpg":"23–24","Seite:LA2-Blitz-0021.jpg":"Tafel","Seite:LA2-Blitz-0022.jpg":"25–26","Seite:LA2-Blitz-0023.jpg":"27–28","Seite:LA2-Blitz-0024.jpg":"29–30","Seite:LA2-Blitz-0025.jpg":"31–32","Seite:LA2-Blitz-0026.jpg":"33–34","Seite:LA2-Blitz-0027.jpg":"35–36","Seite:LA2-Blitz-0028.jpg":"37–38","Seite:LA2-Blitz-0029.jpg":"39–40","Seite:LA2-Blitz-0030.jpg":"Tafel","Seite:LA2-Blitz-0031.jpg":"41–42","Seite:LA2-Blitz-0032.jpg":"43–44","Seite:LA2-Blitz-0033.jpg":"45–46","Seite:LA2-Blitz-0034.jpg":"47–48","Seite:LA2-Blitz-0035.jpg":"49–50","Seite:LA2-Blitz-0036.jpg":"51–52","Seite:LA2-Blitz-0037.jpg":"53–54","Seite:LA2-Blitz-0038.jpg":"55–56","Seite:LA2-Blitz-0039.jpg":"Tafel","Seite:LA2-Blitz-0040.jpg":"Tafel","Seite:LA2-Blitz-0041.jpg":"57–58","Seite:LA2-Blitz-0042.jpg":"59–60","Seite:LA2-Blitz-0043.jpg":"61–62","Seite:LA2-Blitz-0044.jpg":"63–64","Seite:LA2-Blitz-0045.jpg":"65–66","Seite:LA2-Blitz-0046.jpg":"67–68","Seite:LA2-Blitz-0047.jpg":"69–70","Seite:LA2-Blitz-0048.jpg":"71–72","Seite:LA2-Blitz-0049.jpg":"73–74","Seite:LA2-Blitz-0050.jpg":"75–76","Seite:LA2-Blitz-0051.jpg":"77–78","Seite:LA2-Blitz-0052.jpg":"79–80","Seite:LA2-Blitz-0053.jpg":"81–82","Seite:LA2-Blitz-0054.jpg":"83–84","Seite:LA2-Blitz-0055.jpg":"85–86","Seite:LA2-Blitz-0056.jpg":"87–88","Seite:LA2-Blitz-0057.jpg":"Tafel","Seite:LA2-Blitz-0058.jpg":"Tafel","Seite:LA2-Blitz-0059.jpg":"89–90","Seite:LA2-Blitz-0060.jpg":"91–92","Seite:LA2-Blitz-0061.jpg":"93–94","Seite:LA2-Blitz-0062.jpg":"95–96","Seite:LA2-Blitz-0063.jpg":"97–98","Seite:LA2-Blitz-0064.jpg":"99–100","Seite:LA2-Blitz-0065.jpg":"101–102","Seite:LA2-Blitz-0066.jpg":"103–104","Seite:LA2-Blitz-0067.jpg":"105–106","Seite:LA2-Blitz-0068.jpg":"107–108","Seite:LA2-Blitz-0069.jpg":"109–110","Seite:LA2-Blitz-0070.jpg":"111–112","Seite:LA2-Blitz-0071.jpg":"113–114","Seite:LA2-Blitz-0072.jpg":"115–116","Seite:LA2-Blitz-0073.jpg":"117–118","Seite:LA2-Blitz-0074.jpg":"119–120","Seite:LA2-Blitz-0075.jpg":"121–122","Seite:LA2-Blitz-0076.jpg":"123–124","Seite:LA2-Blitz-0077.jpg":"125–126","Seite:LA2-Blitz-0078.jpg":"127–128","Seite:LA2-Blitz-0079.jpg":"129–130","Seite:LA2-Blitz-0080.jpg":"131–132","Seite:LA2-Blitz-0081.jpg":"133–134","Seite:LA2-Blitz-0082.jpg":"135–136","Seite:LA2-Blitz-0083.jpg":"Tafel","Seite:LA2-Blitz-0084.jpg":"137–138","Seite:LA2-Blitz-0085.jpg":"139–140","Seite:LA2-Blitz-0086.jpg":"141–142","Seite:LA2-Blitz-0087.jpg":"143–144","Seite:LA2-Blitz-0088.jpg":"145–146","Seite:LA2-Blitz-0089.jpg":"147–148","Seite:LA2-Blitz-0090.jpg":"149–150","Seite:LA2-Blitz-0091.jpg":"151–152","Seite:LA2-Blitz-0092.jpg":"Tafel","Seite:LA2-Blitz-0093.jpg":"Tafel","Seite:LA2-Blitz-0094.jpg":"153–154","Seite:LA2-Blitz-0095.jpg":"155–156","Seite:LA2-Blitz-0096.jpg":"157–158","Seite:LA2-Blitz-0097.jpg":"159–160","Seite:LA2-Blitz-0098.jpg":"161–162","Seite:LA2-Blitz-0099.jpg":"163–164","Seite:LA2-Blitz-0100.jpg":"165–166","Seite:LA2-Blitz-0101.jpg":"167–168","Seite:LA2-Blitz-0102.jpg":"leer","Seite:LA2-Blitz-0103.jpg":"Tafel","Seite:LA2-Blitz-0104.jpg":"Tafel","Seite:LA2-Blitz-0105.jpg":"leer","Seite:LA2-Blitz-0106.jpg":"169–170","Seite:LA2-Blitz-0107.jpg":"171–172","Seite:LA2-Blitz-0108.jpg":"173–174","Seite:LA2-Blitz-0109.jpg":"175–176","Seite:LA2-Blitz-0110.jpg":"177–178","Seite:LA2-Blitz-0111.jpg":"179–180","Seite:LA2-Blitz-0112.jpg":"181–182","Seite:LA2-Blitz-0113.jpg":"183–184","Seite:LA2-Blitz-0114.jpg":"Tafel","Seite:LA2-Blitz-0115.jpg":"Tafel","Seite:LA2-Blitz-0116.jpg":"Tafel","Seite:LA2-Blitz-0117.jpg":"185–186","Seite:LA2-Blitz-0118.jpg":"187–188","Seite:LA2-Blitz-0119.jpg":"189–190","Seite:LA2-Blitz-0120.jpg":"191–192","Seite:LA2-Blitz-0121.jpg":"193–194","Seite:LA2-Blitz-0122.jpg":"195–196","Seite:LA2-Blitz-0123.jpg":"197–198","Seite:LA2-Blitz-0124.jpg":"199–200","Seite:LA2-Blitz-0125.jpg":"Tafel","Seite:LA2-Blitz-0126.jpg":"Tafel","Seite:LA2-Blitz-0127.jpg":"Tafel","Seite:LA2-Blitz-0128.jpg":"Tafel","Seite:LA2-Blitz-0129.jpg":"Tafel","Seite:LA2-Blitz-0130.jpg":"203–204","Seite:LA2-Blitz-0131.jpg":"205–206","Seite:LA2-Blitz-0132.jpg":"207–208","Seite:LA2-Blitz-0133.jpg":"209–210","Seite:LA2-Blitz-0134.jpg":"211–212","Seite:LA2-Blitz-0135.jpg":"213–214","Seite:LA2-Blitz-0136.jpg":"215–216","Seite:LA2-Blitz-0137.jpg":"217–218","Seite:LA2-Blitz-0138.jpg":"219–220","Seite:LA2-Blitz-0139.jpg":"221–222","Seite:LA2-Blitz-0140.jpg":"223–224","Seite:LA2-Blitz-0141.jpg":"225–226","Seite:LA2-Blitz-0142.jpg":"227–228","Seite:LA2-Blitz-0143.jpg":"229–230","Seite:LA2-Blitz-0144.jpg":"231–232","Seite:LA2-Blitz-0145.jpg":"233–234","Seite:LA2-Blitz-0146.jpg":"235–236","Seite:LA2-Blitz-0147.jpg":"237–238","Seite:LA2-Blitz-0148.jpg":"239–240","Seite:LA2-Blitz-0149.jpg":"241–242","Seite:LA2-Blitz-0150.jpg":"243–244","Seite:LA2-Blitz-0151.jpg":"245–246","Seite:LA2-Blitz-0152.jpg":"247–248","Seite:LA2-Blitz-0153.jpg":"249–250","Seite:LA2-Blitz-0154.jpg":"251–252","Seite:LA2-Blitz-0155.jpg":"253–254","Seite:LA2-Blitz-0156.jpg":"255–256","Seite:LA2-Blitz-0157.jpg":"257–258","Seite:LA2-Blitz-0158.jpg":"259–260","Seite:LA2-Blitz-0159.jpg":"261–262","Seite:LA2-Blitz-0160.jpg":"263–264","Seite:LA2-Blitz-0161.jpg":"Tafel","Seite:LA2-Blitz-0162.jpg":"Tafel","Seite:LA2-Blitz-0163.jpg":"Tafel","Seite:LA2-Blitz-0164.jpg":"Tafel","Seite:LA2-Blitz-0165.jpg":"265–266","Seite:LA2-Blitz-0166.jpg":"267–268","Seite:LA2-Blitz-0167.jpg":"269–270","Seite:LA2-Blitz-0168.jpg":"271–272","Seite:LA2-Blitz-0169.jpg":"273–274","Seite:LA2-Blitz-0170.jpg":"275–276","Seite:LA2-Blitz-0171.jpg":"277–278","Seite:LA2-Blitz-0172.jpg":"279–280","Seite:LA2-Blitz-0173.jpg":"281–282","Seite:LA2-Blitz-0174.jpg":"283–284","Seite:LA2-Blitz-0175.jpg":"285–286","Seite:LA2-Blitz-0176.jpg":"287–288","Seite:LA2-Blitz-0177.jpg":"289–290","Seite:LA2-Blitz-0178.jpg":"291–292","Seite:LA2-Blitz-0179.jpg":"293–294","Seite:LA2-Blitz-0180.jpg":"295–296","Seite:LA2-Blitz-0181.jpg":"297–298","Seite:LA2-Blitz-0182.jpg":"299–300","Seite:LA2-Blitz-0183.jpg":"301–302","Seite:LA2-Blitz-0184.jpg":"303–304","Seite:LA2-Blitz-0185.jpg":"305–306","Seite:LA2-Blitz-0186.jpg":"307–308","Seite:LA2-Blitz-0187.jpg":"309–310","Seite:LA2-Blitz-0188.jpg":"311–312","Seite:LA2-Blitz-0189.jpg":"Tafel","Seite:LA2-Blitz-0190.jpg":"315–316","Seite:LA2-Blitz-0191.jpg":"317–318","Seite:LA2-Blitz-0192.jpg":"319–320","Seite:LA2-Blitz-0193.jpg":"321–322","Seite:LA2-Blitz-0194.jpg":"323–324","Seite:LA2-Blitz-0195.jpg":"325–326","Seite:LA2-Blitz-0196.jpg":"327–328","Seite:LA2-Blitz-0197.jpg":"329–330","Seite:LA2-Blitz-0198.jpg":"331–332","Seite:LA2-Blitz-0199.jpg":"333–334","Seite:LA2-Blitz-0200.jpg":"335–336","Seite:LA2-Blitz-0201.jpg":"337–338","Seite:LA2-Blitz-0202.jpg":"339–340","Seite:LA2-Blitz-0203.jpg":"341–342","Seite:LA2-Blitz-0204.jpg":"343–344","Seite:LA2-Blitz-0205.jpg":"Tafel","Seite:LA2-Blitz-0206.jpg":"Tafel","Seite:LA2-Blitz-0207.jpg":"345–346","Seite:LA2-Blitz-0208.jpg":"347–348","Seite:LA2-Blitz-0209.jpg":"349–350","Seite:LA2-Blitz-0210.jpg":"351–352","Seite:LA2-Blitz-0211.jpg":"353–354","Seite:LA2-Blitz-0212.jpg":"355–356","Seite:LA2-Blitz-0213.jpg":"357–358","Seite:LA2-Blitz-0214.jpg":"359–360","Seite:LA2-Blitz-0215.jpg":"361–362","Seite:LA2-Blitz-0216.jpg":"363–364","Seite:LA2-Blitz-0217.jpg":"365–366","Seite:LA2-Blitz-0218.jpg":"367–368","Seite:LA2-Blitz-0219.jpg":"369–370","Seite:LA2-Blitz-0220.jpg":"371–372","Seite:LA2-Blitz-0221.jpg":"373–374","Seite:LA2-Blitz-0222.jpg":"375–376","Seite:LA2-Blitz-0223.jpg":"Tafel","Seite:LA2-Blitz-0224.jpg":"Tafel","Seite:LA2-Blitz-0225.jpg":"Tafel","Seite:LA2-Blitz-0226.jpg":"Tafel","Seite:LA2-Blitz-0227.jpg":"377–378","Seite:LA2-Blitz-0228.jpg":"379–380","Seite:LA2-Blitz-0229.jpg":"381–382","Seite:LA2-Blitz-0230.jpg":"383–384","Seite:LA2-Blitz-0231.jpg":"385–386","Seite:LA2-Blitz-0232.jpg":"387–388","Seite:LA2-Blitz-0233.jpg":"389–390","Seite:LA2-Blitz-0234.jpg":"391–392","Seite:LA2-Blitz-0235.jpg":"393–394","Seite:LA2-Blitz-0236.jpg":"395–396","Seite:LA2-Blitz-0237.jpg":"397–398","Seite:LA2-Blitz-0238.jpg":"399–400","Seite:LA2-Blitz-0239.jpg":"401–402","Seite:LA2-Blitz-0240.jpg":"403–404","Seite:LA2-Blitz-0241.jpg":"405–406","Seite:LA2-Blitz-0242.jpg":"407–408","Seite:LA2-Blitz-0243.jpg":"Tafel","Seite:LA2-Blitz-0244.jpg":"Tafel","Seite:LA2-Blitz-0245.jpg":"Tafel","Seite:LA2-Blitz-0246.jpg":"Tafel","Seite:LA2-Blitz-0247.jpg":"409–410","Seite:LA2-Blitz-0248.jpg":"411–412","Seite:LA2-Blitz-0249.jpg":"413–414","Seite:LA2-Blitz-0250.jpg":"415–416","Seite:LA2-Blitz-0251.jpg":"417–418","Seite:LA2-Blitz-0252.jpg":"419–420","Seite:LA2-Blitz-0253.jpg":"421–422","Seite:LA2-Blitz-0254.jpg":"423–424","Seite:LA2-Blitz-0255.jpg":"425–426","Seite:LA2-Blitz-0256.jpg":"427–428","Seite:LA2-Blitz-0257.jpg":"429–430","Seite:LA2-Blitz-0258.jpg":"431–432","Seite:LA2-Blitz-0259.jpg":"433–434","Seite:LA2-Blitz-0260.jpg":"435–436","Seite:LA2-Blitz-0261.jpg":"437–438","Seite:LA2-Blitz-0262.jpg":"439–440","Seite:LA2-Blitz-0263.jpg":"Tafel","Seite:LA2-Blitz-0264.jpg":"Tafel","Seite:LA2-Blitz-0265.jpg":"441–442","Seite:LA2-Blitz-0266.jpg":"443–444","Seite:LA2-Blitz-0267.jpg":"445–446","Seite:LA2-Blitz-0268.jpg":"447–448","Seite:LA2-Blitz-0269.jpg":"449–450","Seite:LA2-Blitz-0270.jpg":"451–452","Seite:LA2-Blitz-0271.jpg":"453–454","Seite:LA2-Blitz-0272.jpg":"455–456","Seite:LA2-Blitz-0273.jpg":"457–458","Seite:LA2-Blitz-0274.jpg":"459–460","Seite:LA2-Blitz-0275.jpg":"461–462","Seite:LA2-Blitz-0276.jpg":"463–464","Seite:LA2-Blitz-0277.jpg":"465–466","Seite:LA2-Blitz-0278.jpg":"467–468","Seite:LA2-Blitz-0279.jpg":"469–470","Seite:LA2-Blitz-0280.jpg":"471–472","Seite:LA2-Blitz-0281.jpg":"473–474","Seite:LA2-Blitz-0282.jpg":"475–476","Seite:LA2-Blitz-0283.jpg":"477–478","Seite:LA2-Blitz-0284.jpg":"479–480","Seite:LA2-Blitz-0285.jpg":"481–482","Seite:LA2-Blitz-0286.jpg":"483–484","Seite:LA2-Blitz-0287.jpg":"485–486","Seite:LA2-Blitz-0288.jpg":"487–488","Seite:LA2-Blitz-0289.jpg":"Tafel","Seite:LA2-Blitz-0290.jpg":"489–490","Seite:LA2-Blitz-0291.jpg":"491–492","Seite:LA2-Blitz-0292.jpg":"493–494","Seite:LA2-Blitz-0293.jpg":"495–496","Seite:LA2-Blitz-0294.jpg":"497–498","Seite:LA2-Blitz-0295.jpg":"499–500","Seite:LA2-Blitz-0296.jpg":"501–502","Seite:LA2-Blitz-0297.jpg":"503–504","Seite:LA2-Blitz-0298.jpg":"Tafel","Seite:LA2-Blitz-0299.jpg":"505–506","Seite:LA2-Blitz-0300.jpg":"507–508","Seite:LA2-Blitz-0301.jpg":"509–510","Seite:LA2-Blitz-0302.jpg":"511–512","Seite:LA2-Blitz-0303.jpg":"513–514","Seite:LA2-Blitz-0304.jpg":"515–516","Seite:LA2-Blitz-0305.jpg":"517–518","Seite:LA2-Blitz-0306.jpg":"519–520","Seite:LA2-Blitz-0307.jpg":"Tafel","Seite:LA2-Blitz-0308.jpg":"Tafel","Seite:LA2-Blitz-0309.jpg":"Tafel","Seite:LA2-Blitz-0310.jpg":"Tafel","Seite:LA2-Blitz-0311.jpg":"521–522","Seite:LA2-Blitz-0312.jpg":"523–524","Seite:LA2-Blitz-0313.jpg":"525–526","Seite:LA2-Blitz-0314.jpg":"527–528","Seite:LA2-Blitz-0315.jpg":"529–530","Seite:LA2-Blitz-0316.jpg":"531–532","Seite:LA2-Blitz-0317.jpg":"533–534","Seite:LA2-Blitz-0318.jpg":"535–536","Seite:LA2-Blitz-0319.jpg":"537–538","Seite:LA2-Blitz-0320.jpg":"539–540","Seite:LA2-Blitz-0321.jpg":"541–542","Seite:LA2-Blitz-0322.jpg":"543–544","Seite:LA2-Blitz-0323.jpg":"545–546","Seite:LA2-Blitz-0324.jpg":"547–548","Seite:LA2-Blitz-0325.jpg":"549–550","Seite:LA2-Blitz-0326.jpg":"551–552","Seite:LA2-Blitz-0327.jpg":"553–554","Seite:LA2-Blitz-0328.jpg":"555–556","Seite:LA2-Blitz-0329.jpg":"557–558","Seite:LA2-Blitz-0330.jpg":"559–560","Seite:LA2-Blitz-0331.jpg":"561–562","Seite:LA2-Blitz-0332.jpg":"563–564","Seite:LA2-Blitz-0333.jpg":"565–566","Seite:LA2-Blitz-0334.jpg":"567–568","Seite:LA2-Blitz-0335.jpg":"569–570","Seite:LA2-Blitz-0336.jpg":"571–572","Seite:LA2-Blitz-0337.jpg":"573–574","Seite:LA2-Blitz-0338.jpg":"575–576","Seite:LA2-Blitz-0339.jpg":"577–578","Seite:LA2-Blitz-0340.jpg":"579–580","Seite:LA2-Blitz-0341.jpg":"581–582","Seite:LA2-Blitz-0342.jpg":"583–584","Seite:LA2-Blitz-0343.jpg":"Tafel","Seite:LA2-Blitz-0344.jpg":"Tafel","Seite:LA2-Blitz-0345.jpg":"Tafel","Seite:LA2-Blitz-0346.jpg":"Tafel","Seite:LA2-Blitz-0347.jpg":"585–586","Seite:LA2-Blitz-0348.jpg":"587–588","Seite:LA2-Blitz-0349.jpg":"589–590","Seite:LA2-Blitz-0350.jpg":"591–592","Seite:LA2-Blitz-0351.jpg":"593–594","Seite:LA2-Blitz-0352.jpg":"595–596","Seite:LA2-Blitz-0353.jpg":"597–598","Seite:LA2-Blitz-0354.jpg":"599–600","Seite:LA2-Blitz-0355.jpg":"601–602","Seite:LA2-Blitz-0356.jpg":"603–604","Seite:LA2-Blitz-0357.jpg":"605–606","Seite:LA2-Blitz-0358.jpg":"607–608","Seite:LA2-Blitz-0359.jpg":"609–610","Seite:LA2-Blitz-0360.jpg":"611–612","Seite:LA2-Blitz-0361.jpg":"613–614","Seite:LA2-Blitz-0362.jpg":"615–616","Seite:LA2-Blitz-0363.jpg":"617–618","Seite:LA2-Blitz-0364.jpg":"619–620","Seite:LA2-Blitz-0365.jpg":"621–622","Seite:LA2-Blitz-0366.jpg":"623–624","Seite:LA2-Blitz-0367.jpg":"625–626","Seite:LA2-Blitz-0368.jpg":"627–628","Seite:LA2-Blitz-0369.jpg":"629–630","Seite:LA2-Blitz-0370.jpg":"631–632","Seite:LA2-Blitz-0371.jpg":"633–634","Seite:LA2-Blitz-0372.jpg":"635–636","Seite:LA2-Blitz-0373.jpg":"637–638","Seite:LA2-Blitz-0374.jpg":"639–640","Seite:LA2-Blitz-0375.jpg":"641–642","Seite:LA2-Blitz-0376.jpg":"643–644","Seite:LA2-Blitz-0377.jpg":"645–646","Seite:LA2-Blitz-0378.jpg":"647–648","Seite:LA2-Blitz-0379.jpg":"Tafel","Seite:LA2-Blitz-0380.jpg":"649–650","Seite:LA2-Blitz-0381.jpg":"651–652","Seite:LA2-Blitz-0382.jpg":"653–654","Seite:LA2-Blitz-0383.jpg":"655–656","Seite:LA2-Blitz-0384.jpg":"657–658","Seite:LA2-Blitz-0385.jpg":"659–660","Seite:LA2-Blitz-0386.jpg":"661–662","Seite:LA2-Blitz-0387.jpg":"663–664","Seite:LA2-Blitz-0388.jpg":"665–666","Seite:LA2-Blitz-0389.jpg":"667–668","Seite:LA2-Blitz-0390.jpg":"669–670","Seite:LA2-Blitz-0391.jpg":"671–672","Seite:LA2-Blitz-0392.jpg":"673–674","Seite:LA2-Blitz-0393.jpg":"675–676","Seite:LA2-Blitz-0394.jpg":"677–678","Seite:LA2-Blitz-0395.jpg":"679–680","Seite:LA2-Blitz-0396.jpg":"681–682","Seite:LA2-Blitz-0397.jpg":"683–684","Seite:LA2-Blitz-0398.jpg":"685–686","Seite:LA2-Blitz-0399.jpg":"687–688","Seite:LA2-Blitz-0400.jpg":"689–690","Seite:LA2-Blitz-0401.jpg":"691–692","Seite:LA2-Blitz-0402.jpg":"693–694","Seite:LA2-Blitz-0403.jpg":"695–696","Seite:LA2-Blitz-0404.jpg":"Tafel","Seite:LA2-Blitz-0405.jpg":"Tafel","Seite:LA2-Blitz-0406.jpg":"Tafel","Seite:LA2-Blitz-0407.jpg":"Tafel","Seite:LA2-Blitz-0408.jpg":"697–698","Seite:LA2-Blitz-0409.jpg":"699–700","Seite:LA2-Blitz-0410.jpg":"701–702","Seite:LA2-Blitz-0411.jpg":"703–704","Seite:LA2-Blitz-0412.jpg":"705–706","Seite:LA2-Blitz-0413.jpg":"707–708","Seite:LA2-Blitz-0414.jpg":"709–710","Seite:LA2-Blitz-0415.jpg":"711–712","Seite:LA2-Blitz-0416.jpg":"713–714","Seite:LA2-Blitz-0417.jpg":"715–716","Seite:LA2-Blitz-0418.jpg":"717–718","Seite:LA2-Blitz-0419.jpg":"719–720","Seite:LA2-Blitz-0420.jpg":"721–722","Seite:LA2-Blitz-0421.jpg":"723–724","Seite:LA2-Blitz-0422.jpg":"725–726","Seite:LA2-Blitz-0423.jpg":"727–728","Seite:LA2-Blitz-0424.jpg":"Tafel","Seite:LA2-Blitz-0425.jpg":"Tafel","Seite:LA2-Blitz-0426.jpg":"Tafel","Seite:LA2-Blitz-0427.jpg":"Tafel","Seite:LA2-Blitz-0428.jpg":"729–730","Seite:LA2-Blitz-0429.jpg":"731–732","Seite:LA2-Blitz-0430.jpg":"733–734","Seite:LA2-Blitz-0431.jpg":"735–736","Seite:LA2-Blitz-0432.jpg":"737–738","Seite:LA2-Blitz-0433.jpg":"739–740","Seite:LA2-Blitz-0434.jpg":"741–742","Seite:LA2-Blitz-0435.jpg":"743–744","Seite:LA2-Blitz-0442.jpg":"745–746","Seite:LA2-Blitz-0443.jpg":"747–748","Seite:LA2-Blitz-0436.jpg":"749–750","Seite:LA2-Blitz-0437.jpg":"751–752","Seite:LA2-Blitz-0438.jpg":"753–754","Seite:LA2-Blitz-0439.jpg":"755–756","Seite:LA2-Blitz-0440.jpg":"757–758","Seite:LA2-Blitz-0441.jpg":"759–760",}

for i in pages:
    print(i)
    page = pywikibot.Page(site, i)
    fit1 = re.search("–", pages[i])
    if fit1:
        tempText = re.sub("\{\{Zitierempfehlung\|.*\|.*\}\}", "{{Zitierempfehlung|Projekt=Meyers Blitz-Lexikon. Die Schnellauskunft für jedermann in Wort und Bild., Leipzig 1932|Seite=Spalten %s|FLAG=ON}}" % pages[i], page.text)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: Zitierempfehlung korrigiert', botflag=True, )